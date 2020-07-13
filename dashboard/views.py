from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers

from django.views.decorators.csrf import csrf_exempt
from .models import ClimateZone, EGRID, ZipcodeCounty, GWP, CED, HomeESS, MicrogridESS, Fastcharger, ElectricConsumption, CustomESS, TouMatrix
import requests
import json
from BPTK_Py import bptk
import BPTK_Py.config as config
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import math
matplotlib.use("Agg")
from pymoo.model.problem import Problem
from pymoo.algorithms.so_genetic_algorithm import GA

#from pymoo.algorithms.so_nelder_mead import NelderMead
#from pymoo.algorithms.so_nelder_mead import NelderAndMeadTermination
#from pymoo.algorithms.so_de import dea
from pymoo.optimize import minimize
import warnings  # To remove the warnings fro

import os
from dotenv import load_dotenv

import pvlib

load_dotenv()

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = PROJECT_DIR.replace("\\", "/")
PROJECT_DIR = PROJECT_DIR[:-10]
PROJECT_DIR += '/static'

bptk = bptk()

#touMatrix = TouMatrix()
#elecConsump = ElectricConsumption()
customEss = CustomESS()

# Create your views here.
def dashboard(request):
    return render(request, 'dashboard.html')

def calc_cost(real_discnt,year_analysis,npv,Elec_consumption_matrix):
    I=real_discnt/100
    
    #Capital recovery factor 
    CRF=(I*(1+I)**year_analysis)/(((1+I)**year_analysis)-1)
    
    #Calculating annualized cost
    AC=CRF*npv
    
    #Calculating LCOE
    LCOE=AC/(np.sum(Elec_consumption_matrix)/year_analysis) 
    
    return AC,LCOE

def calc_cashflow(pv_cost,batt_cost,inverter_cost,batt_replc_hour,batt_replc,year_analysis,pv_onm,batt_onm,invrtr_onm,base_connec_cost,sales_tax_perc,liab_insu_fee,pv_salv,batt_salv,inv_salv,cost_of_buy_elec,total_net_met_benf,total_feed_in_tarff_benf,arbit_solar_panel_size,capacity_of_batt_module,inverter_cap):
    #Flattening all the matrices as it would be easier to work with vectors
    elec_vector=cost_of_buy_elec.flatten('F')
    NM_vect=total_net_met_benf.flatten('F')
    FIT_vect=total_feed_in_tarff_benf.flatten('F')
    
    #Calculating the year when battery got replaced
    batt_rep_year=batt_replc_hour/8760
    
    #Empty numpy arrays that will hold the cash flow diagrams of each part 
    cash_flow_elec=np.zeros([1,year_analysis+1])
    cash_flow_NM=np.zeros([1,year_analysis+1])
    cash_flow_FIT=np.zeros([1,year_analysis+1])
    cash_flow_liab=np.zeros([1,year_analysis+1])
    cash_flow_comp=np.zeros([1,year_analysis+1])
    cash_flow_onm=np.zeros([1,year_analysis+1])
    
    counter=0
    
    #Loops run to create cash flow diagrams for all costs related to grid purchases, net metering and feed in tariff
    for i in range(year_analysis):
        #Accounting for Electricity bought, Base connection fee and Sales tax 
        cash_flow_elec[0,i+1]=-(np.sum(elec_vector[0+(365*24*counter):(365*24+365*24*counter)])+base_connec_cost*12+(sales_tax_perc/100)*(np.sum(elec_vector[0+(365*24*counter):(365*24+365*24*counter)])))
        
        #Cash flow for net metering
        cash_flow_NM[0,i+1]=np.sum(NM_vect[0+(365*24*counter):(365*24+365*24*counter)])
        
        #Cash flow for FIT
        cash_flow_FIT[0,i+1]=np.sum(FIT_vect[0+(365*24*counter):(365*24+365*24*counter)])
        
        #Cash flow for Liability insurance
        cash_flow_liab[0,i+1]=-1*liab_insu_fee*12
        
        
        #Cash flow for operation and maintainence
        cash_flow_onm[0,i+1]=-(pv_onm*arbit_solar_panel_size+batt_onm*capacity_of_batt_module+invrtr_onm*inverter_cap)
        
            
        counter+=1
    
    
    #Cash flow diagrams for PV , Battery and inverter
    cash_flow_comp[0,0]=-(pv_cost+batt_cost+inverter_cost)
    cash_flow_comp[0,year_analysis]=pv_salv+batt_salv+inv_salv
    
    #Check if the battery has been replaced at all
    
    if (batt_replc>0):
        
        chng_year=math.floor(batt_rep_year)
    
        cash_flow_comp[0,chng_year]=-batt_cost

    return cash_flow_elec,cash_flow_NM,cash_flow_FIT,cash_flow_liab,cash_flow_onm,cash_flow_comp

def calc_npv(year_analysis,pv_cost,inverter_cost,batt_cost,batt_replc_hour,base_connec_cost,batt_replc,sales_tax_perc,liab_insu_fee,one_time_conec_fee,pv_onm,batt_onm,invrtr_onm,cost_of_buy_elec,total_net_met_benf,total_feed_in_tarff_benf,discnt_rate,infl_rate,pv_lifetime,invrtr_lifetime,arbit_solar_panel_size,capacity_of_batt_module,inverter_cap):
    
    batt_rep_year=batt_replc_hour/8760
    chng_year=(math.floor(batt_rep_year))
    
    real_discnt=discnt_rate-infl_rate
    I=real_discnt/100
    
    
    #The NPV of component cost is the same as the original cost as all components were bought in the first year
    npv_cmpnt=pv_cost+batt_cost+inverter_cost
    
    if (batt_replc!=0):
        npv_cmpnt=npv_cmpnt+(batt_cost/((1+I)**(chng_year)))
    
    
    #This loop calculates the net present value of electricity bought each year
    
    #Initialize the value of npv_elec with the first year's amount (Formula is applied only after second year)
    
    elec_bought_vector=cost_of_buy_elec.flatten('F')
    npv_elec=np.sum(elec_bought_vector[0:365*24])/(1+I)
    
    #Remove plot after testing
    np_this_year_list=[]
    np_this_year_list.append(npv_elec)
    count=365
    for el in range(year_analysis-1):
        
        cost_of_elec_this_year=elec_bought_vector[count*24:(365*24)+count*24]
        npv_elec_this_year=np.sum(cost_of_elec_this_year)/((1+I)**(el+2))
        np_this_year_list.append(npv_elec_this_year)
        npv_elec=npv_elec+npv_elec_this_year
        
        
        
        count+=365
    # =============================================================================
    # 
    # #plt.ylim(0,1000)
    # plt.plot(elec_bought_vector)
    # 
    # plt.ylabel('Net present value each year')
    # plt.xlabel('Year')
    # plt.show()  
    # =============================================================================
    
    #This loop calculates the net present value of net metering amount each year
       
    net_met_vector=total_net_met_benf.flatten('F')
    npv_net_met=np.sum(net_met_vector[0:365*24])/(1+I)
    
    count_1=365
    
    for el in range(year_analysis-1):
        
        net_met_year=net_met_vector[count_1*24:(365*24)+count_1*24]
        npv_net_met_year=np.sum(net_met_year)/((1+I)**(el+2))
        npv_net_met=npv_net_met+npv_net_met_year
        
        count_1+=365
        
     
        
            
    #This loop calculates the net present value of FIT amount each year
    FIT_vector=total_feed_in_tarff_benf.flatten('F')
    npv_FIT=np.sum(FIT_vector[0:365*24])/(1+I)
    count_2=365
    
    for el in range(year_analysis-1):
        
        FIT_year=FIT_vector[count_2*24:(365*24)+count_2*24]
        npv_FIT_year=np.sum(FIT_year)/((1+I)**(el+2))
        npv_FIT=npv_FIT+npv_FIT_year
        
        count_2+=365
        
    #Calculate the net present value of the base connec cost 
    base_connec_cost_year=base_connec_cost*12
    npv_bas_conn=(base_connec_cost_year)*((1-(1+I)**(-year_analysis))/I)
    
    #Calculate the net present value of the O & M cost
    onm_year=pv_onm*arbit_solar_panel_size+batt_onm*capacity_of_batt_module+invrtr_onm*inverter_cap
    
    npv_onm=(onm_year)*((1-(1+I)**(-year_analysis))/I)
    
    #Calculating the salvage value of the components 
    pv_salv=pv_cost*((pv_lifetime-year_analysis)/pv_lifetime)
    
    
    
    #Making sure that batt salvage value is never negative
    if(batt_replc==0 and batt_rep_year==0): # For the special consition when the analysis is ran for 5 years against a battery which gets replaced at the end of 5 years
        
        batt_salv=0
        
    
    
    elif (batt_replc!=0 and (year_analysis%batt_rep_year)==0):
        
        #batt_salv=batt_cost*((5-batt_rep_year)/5)
        batt_salv=0
    
    elif (batt_replc==0): #This codition is to make sure correct salvage value in case the battery gets replaced at exactly the same time when the analysis ends
        batt_salv=batt_cost*((5-batt_rep_year)/5)
        
    else:
        temp=math.trunc(year_analysis/(batt_replc*batt_rep_year))
        batt_salv=batt_cost*((5-temp)/5)
                             
    if (batt_salv<0):
        batt_salv=0                        
     
    
    inv_salv=inverter_cost*((invrtr_lifetime-year_analysis)/invrtr_lifetime)
    #Making sure that inverter salvage value is  never negative\
    if (inv_salv<0):
        inv_salv=0
    
    
    comp_salv=(pv_salv/((1+I)**(year_analysis)))+(batt_salv/((1+I)**(year_analysis)))+(inv_salv/((1+I)**(year_analysis)))
    
    
    
    #Calculating NPV for the Monthly sales tax on bill
    npv_sal_tax=((np.sum(elec_bought_vector[0:365*24]))*(sales_tax_perc/100))/(1+I)
    count_3=365
    for el in range(year_analysis-1):
        sal_tax_this_year=(np.sum(elec_bought_vector[count_3*24:(365*24)+count_3*24]))*(sales_tax_perc/100)
        npv_sal_tax_this_year=(sal_tax_this_year)/((1+I)**(el+2))
        npv_sal_tax=npv_sal_tax+npv_sal_tax_this_year
    
    
    #Calculating NPV for liability insurance fee
    liab_year=liab_insu_fee*12
    npv_liab=(liab_year)*((1-(1+I)**(-year_analysis))/I)
    
    
    npv=npv_cmpnt+npv_elec-npv_net_met-npv_FIT+npv_bas_conn+npv_onm-comp_salv+npv_sal_tax+npv_liab+one_time_conec_fee 
    
   
    return npv,pv_salv,batt_salv,inv_salv

def calc_pvlib_irrad(lat,lng,gamma_s,t_z,tilt,soil_shad_loss):

    """===These values are obtained from the files and then transferrred to the function ===================================================="""
    
    file_location='static'
    weather_file_name='/samples/Detroit_TMY3_weather_data.csv'
    
    if t_z[3] == '-':
        t_z = 'Etc/GMT+' + t_z[-1]
    else:
        t_z = 'Etc/GMT-' + t_z[-1]

    print("timezone",t_z)
    tim_stmp=pd.read_csv('home/ray/ford/static/samples/Detroit_TMY3_weather_data.csv',usecols=[0],skiprows=1,)
    tim_stmp=pd.date_range('1988-01-01',periods=8760,freq='H')
    tim_stmp=tim_stmp.tz_localize(t_z)

    
    #calling in the values of direct normal irradiance
    dni=pd.read_csv(file_location + weather_file_name,usecols=[7],skiprows=1,)
    dni_vector=dni.as_matrix()
    
    #Calling in the values of DHI
    dhi=pd.read_csv(file_location + weather_file_name,usecols=[10],skiprows=1,)
    dhi_vector=dhi.as_matrix()
    
    #Calling in the values of GHI
    ghi=pd.read_csv(file_location + weather_file_name,usecols=[4],skiprows=1,)
    ghi_vector=ghi.as_matrix()
    
    
    #Calling in the values of extraterrestrial irradiance
    extra_dni=pd.read_csv(file_location + weather_file_name,usecols=[1],skiprows=1,)
    extra_dni_vector=extra_dni.as_matrix()
    
    #Finding out the elevation value from the weather file 
    ele=pd.read_csv(file_location + weather_file_name,index_col=[0],header=None,error_bad_lines=False,warn_bad_lines=False)
    elev=float(ele.values[0,5])

    
    albdo=0.2
    loss=(100-soil_shad_loss)/100
    
    
    
    #Empty Lists
    tot_irrad=np.zeros((8760,1))
    
    for i in range(8760):
        
        
        
        my_azm=pvlib.solarposition.pyephem(tim_stmp[[i]],latitude=lat,longitude=lng,altitude=elev,pressure=101325,temperature=9.4,horizon='+0:00')
        
        
        irrad_comp=pvlib.irradiance.get_total_irradiance(surface_tilt=tilt,surface_azimuth=gamma_s,solar_zenith=my_azm.zenith,solar_azimuth=my_azm.azimuth,dni=dni_vector[i],ghi=ghi_vector[i],dhi=dhi_vector[i],dni_extra=extra_dni_vector[i],airmass=None,albedo=albdo,surface_type=None,model='isotropic')                         
        tot_irrad[i]=(loss*(irrad_comp.poa_global))/1000

    
    return tot_irrad


def calc_env_impact(year_analysis,arbit_solar_panel_size,pv_lifetime,invrtr_lifetime,capacity_of_batt_module,batt_replc,batt_replc_hour,batt_rplcmt_year,ILR,elec_bought_grid,total_net_met_benf,rate_matrix,total_feed_in_tarff_benf,feed_in_tariff_rate,PV_GWP,PV_CED,Batt_GWP,Batt_CED,Inv_GWP,Inv_CED,Elec_GWP,Elec_CED):
    
    #First condition when the battery does not get replaced at all 
    if (batt_replc==0):
        gwp_impact=arbit_solar_panel_size*PV_GWP*(year_analysis/pv_lifetime)+(arbit_solar_panel_size/ILR)*Inv_GWP*(year_analysis/invrtr_lifetime)+capacity_of_batt_module*Batt_GWP+np.nansum(elec_bought_grid)*Elec_GWP-np.nansum((total_net_met_benf/rate_matrix))*Elec_GWP-np.nansum((total_feed_in_tarff_benf/feed_in_tariff_rate))*Elec_GWP
        
        ced_impact=arbit_solar_panel_size*PV_CED*(year_analysis/pv_lifetime)+(arbit_solar_panel_size/ILR)*Inv_CED*(year_analysis/invrtr_lifetime)+capacity_of_batt_module*Batt_CED+np.nansum(elec_bought_grid)*Elec_CED-np.nansum((total_net_met_benf/rate_matrix))*Elec_CED-np.nansum((total_feed_in_tarff_benf/feed_in_tariff_rate))*Elec_CED
    else:
        replc_year=batt_replc_hour/8760
        
        rep_batt_gwp_impact=capacity_of_batt_module*batt_replc*(replc_year/batt_rplcmt_year)*Batt_GWP
        
        gwp_impact=arbit_solar_panel_size*PV_GWP*(year_analysis/pv_lifetime)+(arbit_solar_panel_size/ILR)*Inv_GWP*(year_analysis/invrtr_lifetime)+capacity_of_batt_module*Batt_GWP+np.nansum(elec_bought_grid)*Elec_GWP-np.nansum((total_net_met_benf/rate_matrix))*Elec_GWP-np.nansum((total_feed_in_tarff_benf/feed_in_tariff_rate))*Elec_GWP
    
        gwp_impact=gwp_impact+rep_batt_gwp_impact
        
        rep_batt_ced_impact=capacity_of_batt_module*batt_replc*(replc_year/batt_rplcmt_year)*Batt_CED
        
        ced_impact=arbit_solar_panel_size*PV_CED*(year_analysis/pv_lifetime)+(arbit_solar_panel_size/ILR)*Inv_CED*(year_analysis/invrtr_lifetime)+capacity_of_batt_module*Batt_CED+np.nansum(elec_bought_grid)*Elec_CED-np.nansum((total_net_met_benf/rate_matrix))*Elec_CED-np.nansum((total_feed_in_tarff_benf/feed_in_tariff_rate))*Elec_CED
        
        ced_impact=ced_impact+rep_batt_ced_impact
        
    
    return gwp_impact,ced_impact
    
def baseline(year_analysis,discnt_rate,infl_rate,sales_tax_perc,base_fee_conec_cost,one_time_conec_fee,Elec_consumption_matrix,rate_matrix,Elec_GWP,Elec_CED):
    
    real_discnt=discnt_rate-infl_rate
    I=real_discnt/100
    
    
    hourly_elec_bought_cost=np.multiply(Elec_consumption_matrix,rate_matrix)
    
    hrly_elec_price_vector=hourly_elec_bought_cost.flatten('F')
    
    
    #Initialize the value of net present value  with the first year's amount (Formula is applied only after second year)
    
    net_present_elec=np.sum(hrly_elec_price_vector[0:8760])/(1+I)
    
    count=365
    for el in range(year_analysis-1):
        
        cost_of_elec_this_year=hrly_elec_price_vector[count*24:(365*24)+count*24]
        npv_elec_this_year=np.sum(cost_of_elec_this_year)/((1+I)**(el+2))
        
        net_present_elec=net_present_elec+npv_elec_this_year
        
        count+=365
        
    
    #Calculating NPV for the Monthly sales tax on bill
    net_present_sales_tax=((np.sum(hrly_elec_price_vector[0:8760]))*(sales_tax_perc/100))/(1+I)
    
    count_3=365
    for el in range(year_analysis-1):
        sal_tax_this_year=(np.sum(hrly_elec_price_vector[count_3*24:(365*24)+count_3*24]))*(sales_tax_perc/100)
        npv_sal_tax_this_year=(sal_tax_this_year)/((1+I)**(el+2))
        net_present_sales_tax=net_present_sales_tax+npv_sal_tax_this_year
        
    #Calculate the net present value of the base connec cost 
    base_connec_cost_year=base_fee_conec_cost*12
    net_present_base_con_cost=(base_connec_cost_year)*((1-(1+I)**(-year_analysis))/I)
    
    npv=net_present_base_con_cost+np.sum(net_present_elec)+np.sum(net_present_sales_tax)+one_time_conec_fee
    
    CRF=(I*(1+I)**year_analysis)/(((1+I)**year_analysis)-1)
    
    base_AC=CRF*npv
    
    base_LCOE=base_AC/(np.sum(Elec_consumption_matrix)/year_analysis)
    
    
    base_GWP=np.sum(np.multiply(Elec_consumption_matrix,Elec_GWP))
    
    base_CED=np.sum(np.multiply(Elec_consumption_matrix,Elec_CED))
    
    return base_AC,base_LCOE,base_GWP,base_CED

def load(request, format=None):
    
    _zipcode = request.POST['zipcode']
    _state = request.POST['state']
    _year = request.POST['year']
    _file = request.POST.get('file')
    _fileCheck = bool(int(request.POST.get('filecheck')))

    if _fileCheck:
        customEss.set_array(json.loads(_file))

    zipcode_county = ZipcodeCounty.objects.filter(zip_code=int(_zipcode)).first()
    county_name = zipcode_county.county_name[:-7]

    climate_zone = ClimateZone.objects.get(county_name=county_name, state=_state)

    e_grid = EGRID.objects.get(zip_code = int(_zipcode))
    e_grid_code = e_grid.eGRID_subregion

    gwp = GWP.objects.get(year=_year, eGRID_subregion=e_grid_code)
    ced = CED.objects.get(year=_year, eGRID_subregion=e_grid_code)

    check = serializers.serialize('json',[gwp,ced,climate_zone])
    struct = json.loads(check)
    data = json.dumps(struct[:])
    

    return HttpResponse(data, content_type='json')
    #return HttpResponse('')


def matrixDatabase(request, format=None):
    #print('received database for matrix')
    _fileCheck = bool(int(request.POST.get('filecheck')))
    system_app = request.POST.get('system_app')
    climate_zone = request.POST.get('climate_zone')
    zone_number = 'Zone_' + str(climate_zone)
    if _fileCheck != True:
        if system_app == 'home-ESS':
            zone_list = HomeESS.objects.get(zone_number=zone_number).array_list
        elif system_app == 'micro-ESS':
            zone_list = MicrogridESS.objects.get(zone_number=zone_number).array_list
        elif system_app == 'fast-charger':
            zone_list = Fastcharger.objects.get().watt
        else: #when it is home-charger
            zone_list = HomeESS.objects.get(zone_number=zone_number).array_list
        zone_list = zone_list.strip('][').split(', ')
        for i in range(len(zone_list)):
            zone_list[i] = float(zone_list[i].strip("'"))
    else:
        zone_list = customEss.array_list
        if len(zone_list) > 8760:
            zone_list = zone_list[:8760]
        elif len(zone_list) < 8760:
            for i in range(len(zone_list),8760):
                zone_list.append(0.0)

    return HttpResponse(json.dumps(zone_list))

def assignDatabase(request, format=None):
    TouMatrix.objects.all().delete()
    ElectricConsumption.objects.all().delete()

    TouMatrix.objects.create(array_list=request.POST.get('rateList'))
    ElectricConsumption.objects.create(array_list=request.POST.get('zoneList'))
    #touMatrix.set_array(json.loads(request.POST.get('rateList')))
    #elecConsump.set_array(json.loads(request.POST.get('zoneList')))
    touList = TouMatrix.objects.all().first().array_list
    return HttpResponse(touList)
    
def calc(request):
    #print("here")

    #check = HomeESS.objects.get(Zone_1='Zone_1')
    #print("check", elecConsump.array_list[:360])
    touMatrix = request.POST.get('tou-matrix')
    elecArray = request.POST.get('elecArray')

    _zipcode = request.POST['zipcode']
    _state = request.POST['state']
    _proj_lifetime = request.POST['proj-lifetime']
    _year = request.POST['year']
    _system_app = request.POST['system-app']
    t_z = request.POST['t_z']

    _pop_size = request.POST['pop-size']
    _calc_amount = request.POST['calc-amount']

    _conn_fee = request.POST['conn-fee']
    _elec_price_change = request.POST['elec-price-change']
    _feed_in_tariff = request.POST['feed-in-tariff']
    _feed_in_tariff_rate = request.POST['feed-in-tariff-rate']

    _net_metering = request.POST['net-metering']
    _sales_tax_perc = request.POST['sales-tax-perc']
    _one_time_conec_fee = request.POST['one-time-conec-fee']
    _elec_GWP = request.POST['Elec-GWP']
    _liab_insu_fee = request.POST['liab-insu-fee']
    _elec_CED = request.POST['Elec-CED']
    _discnt_rate = request.POST['discnt_rate']
    _infl_rate = request.POST['infl_rate']

    _pv_cost = request.POST['PV-cost']
    _pv_effi = request.POST['PV-effi']
    _inv_cost = request.POST['inv-cost']
    _inv_effi = request.POST['inv-effi']
    _max_power_coeff = request.POST['max-power-temp-coeff']
    _pv_onm = request.POST['pv-onm']
    _gamma_s = request.POST['gamma-s']
    _tilt = request.POST['tilt-value']
    _soil_shad_loss = request.POST['soil-shad-loss']
    _pv_GWP = request.POST['PV-GWP']
    _pv_lower_limit = request.POST['pv-lower-limit']
    _pv_CED = request.POST['PV-CED']
    _pv_upper_limit = request.POST['pv-upper-limit']
    _pv_lifetime = request.POST['pv-lifetime']
    _invrtr_lifetime = request.POST['invrtr-lifetime']
    _annual_invert_op_main = request.POST['annual-invert-op-main']
    _inv_GWP = request.POST['inv-GWP']
    _invert_load_ratio = request.POST['invert-load-ratio']
    _inv_CED = request.POST['inv-CED']

    _bat_cost = request.POST['bat-cost']
    _bat_effi = request.POST['bat-effi']
    _bat_warranty = request.POST['bat-warranty']
    _annual_bat_op_main = request.POST['annual-bat-op-main']
    _voltage = request.POST['voltage']
    _maximum_depth_discharge = request.POST['maximum-depth-discharge']
    _cap_ea_string = request.POST['cap-ea-string']
    _max_allow_per_kwh = request.POST['max-allow-per-kwh']
    _bat_GWP = request.POST['glob-warm-pot-bat']
    _bat_lower_limit = request.POST['bat-lower-limit']
    _cal_ageing_param = request.POST['cal-ageing-param']
    _bat_CED = request.POST['cum-energy-demand-bat']
    _bat_upper_limit = request.POST['bat-upper-limit']
    _cyclic_ageing_param = request.POST['cyclic-ageing-param']

    _lat = request.POST['lat']
    _long = request.POST['long']

    zipcode_county = ZipcodeCounty.objects.filter(zip_code=int(_zipcode)).first()
    county_name = zipcode_county.county_name[:-7]

    climate_zone = ClimateZone.objects.get(county_name=county_name, state=_state)
    climate_zone_code = climate_zone

    e_grid = EGRID.objects.get(zip_code = int(_zipcode))
    e_grid_code = e_grid.eGRID_subregion

    gwp = GWP.objects.get(year=_year, eGRID_subregion=e_grid_code)
    gwp_coef = gwp.gwp

    ced = CED.objects.get(year=_year, eGRID_subregion=e_grid_code)
    ced_coef = ced.ced

    pv_lower_limit = int(_pv_lower_limit)
    pv_upper_limit = int(_pv_upper_limit)
    bat_lower_limit = int(_bat_lower_limit)
    bat_upper_limit = int(_bat_upper_limit)

    pop_size = int(_pop_size)
    calc_amount = int(_calc_amount)

    print("pop size", pop_size)
    print("calc amount", calc_amount)
    
    #print("here start pvlib irrad")
    #calc_pvlib_irrad(float(_lat),float(_long),float(_gamma_s),t_z,float(_tilt),int(_soil_shad_loss))
    #const={"ghi_column_vector":calc_pvlib_irrad(float(_lat),float(_long),float(_gamma_s),t_z,float(_tilt),int(_soil_shad_loss))}
    const = {"ghi_column_vector": np.zeros((8760,1))}
    def evaluate(x, const):
        arbit_solar_panel_size, capacity_of_batt_module = x

        #arbit_solar_panel_size=1.635 #For now assuming this in squae meteres 
        #capacity_of_batt_module=10 # in KWh 
        
        pv_module_efficiency=round(float(_pv_effi) / 100, 2)   # (UI)modules conversion efficinecy
        max_power_temp_coeff=float(_max_power_coeff) #Maximum power temperature cofficient
        cell_temp=50 #critical temperature of the cell assumed constant for now i.e. 
        year_analysis=int(_proj_lifetime)

        lat = float(_lat)
        lng = float(_long)


        cost_of_batt_module_per_kWh=int(_bat_cost)  # Cost of one battery module per kWh in dollars (This is just an assumption)
        inverter_ccost_per_kw = 100
        cost_of_solar_panel=int(_pv_cost)  #(UI) Cost of solar panel in dollars (adopted from earler HOMER models)
        base_fee_conec_cost=float(_conn_fee)  #(UI) need to look this up (For the purpose of trial this thing has been kept as 82.5 cents, the same as mentioned in the Liet al , 2018 )
        sales_tax_perc = float(_sales_tax_perc)
        liab_insu_fee = int(_liab_insu_fee)
        one_time_conec_fee = int(_one_time_conec_fee)
        net_metering_tou_percentage = 100
        pv_onm = int(_pv_onm)
        batt_onm = int(_annual_bat_op_main)
        invrtr_onm = int(_annual_invert_op_main)
        discnt_rate = float(_discnt_rate)
        infl_rate = float(_infl_rate)
        real_discnt=discnt_rate-infl_rate


        tilt = float(_tilt)
        gamma_s = float(_gamma_s)
        pv_panel_area=(10/1.5)*arbit_solar_panel_size
        feed_in_tariff_rate = float(_feed_in_tariff_rate)
        percent_inc_in_elec_price= int(_elec_price_change)  # (UI)enter the annual percentage in electriciy prices here 
        alpha_cap = float(_cal_ageing_param)
        beta_cap = float(_cyclic_ageing_param)
        day_stamp=1
        voltage=float(_voltage)
        throughput_limit = int(_max_allow_per_kwh)
        thrpt_replacement = throughput_limit/voltage
        batt_rplcmt_year=5
        max_alow_dod=int(_maximum_depth_discharge)
        minm_bat_capac=(100-max_alow_dod)/100
        string_capacity=float(_cap_ea_string)
        batt_rtrip_eff=91.3
        ILR=2.9
        invert_eff=98
        pv_lifetime=int(_pv_lifetime)
        invrtr_lifetime=int(_invrtr_lifetime)
        soil_shad_loss=int(_soil_shad_loss)

        max_bought_elec_grid=1000

        #Switch statement for FIT or net metering (1 is on and 0 is off, both net metering and FIT can not be on simulatenously)
        net_metering=int(_net_metering)
        feed_in_tariff=int(_feed_in_tariff)

        #Switch function for optimizing cost or environemental impacts
        Cost=0
        carbn_ftprnt=0
        cum_dem=0

        #Variable for environmental impact function
        PV_GWP=float(_pv_GWP)
        Inv_GWP=float(_inv_GWP)
        PV_CED=float(_pv_CED)
        Inv_CED=float(_inv_CED)
        Elec_GWP=float(_elec_GWP)
        Elec_CED=float(_elec_CED)
        Batt_GWP=float(_bat_GWP)  
        Batt_CED=float(_bat_CED)
        #print("HERE ---------")
        #print(len(touMatrix),type(touMatrix))
        #touMatrix = TouMatrix.objects.all().first().array_list.strip('][').split('], [')
        #elecConsump = ElectricConsumption.objects.all().first().array_list.strip('][').split(',')
        #print("THIS IS FKING SIZE ONE ARRAY: ", len(touMatrix))
        #print(touMatrix[:2])
            
        #elecConsump = list(map(float,elecConsump))
        #print("THIS IS FKING TYPE: ", type(elecConsump))
        #print("THIS IS FKING YES: ", elecConsump[:300])
        #print("ELECT:",Elec_GWP, Elec_CED)
        """==============================================================================================================================="""
        """Empty arrays/matrices created to account for holding the battery capacity and state of charge of battery in each hour"""
        soc_vect= np.zeros((8760*year_analysis,1)) # An empty numpy array created to hold the State of charge of the battery throughout the optmization
        curnt_batt_capac=np.zeros((8760*year_analysis,1))  #Empty numpy array to hold the values of the current battery capcity at any moment with refenrce to degradation
        buy_elec=np.zeros((8760*year_analysis,1))   #Empty numpy array to hold the amoutn of electricity bought from the grid
        
        """==============================================================================================================================="""

        """============================================================================================================================="""       
        """ function to caluclte the battery charging in one day """ 
        
        """The following code loads an excel  file of hourly consumption into python and converts into a 24 by 365 numercial matrix """

        Elec_consumption_dataframe=pd.DataFrame(0) # the file is uploaded in python in form of a dataframe 
        
        Elec_consumption_matrix=Elec_consumption_dataframe.as_matrix() # dataframe converted in workaable matix format
        
        Transposed_elec_consumption_vector=Elec_consumption_matrix.transpose() #transposed the column vector into row vector
        
        Elec_consumption_matrix=np.reshape(Transposed_elec_consumption_vector,(24,365),order='F')  #the last parameter will place it in Fortran like orde  
        
        Elec_consumption_matrix=np.tile(Elec_consumption_matrix,year_analysis)      # The matrix has been made a giant matrix of 

        """ The follwing code loads loads an excel file of GHI, wind and dry bulb temperature data into python and converts it into a 24 by 365 numerical matrix """
        
        
        """=====================================================GHI data================================================================================================================"""
       
        #Importing the values of direct Normal Irradiance
        #dni=pd.read_csv(file_location + weather_file_name,usecols=[7],skiprows=1,) # downloading GHI data in the python dataframe
        
        #Converting DNI values in the KW/m2 format and workable matrix format
    
        #dni_dataframe=dni/1000 
        #dni_vector=dni_dataframe.as_matrix()
        
        
        #Importing the values of diffused horizontal irradiance 
        #dhi=pd.read_csv(file_location + weather_file_name,usecols=[19],skiprows=1,)
        
        #Converting DhI values in the KW/m2 format and workable matrix format
        #dhi_dataframe=dhi/1000
        #dhi_vector=dhi_dataframe.as_matrix()
        
        #Calling the PV gnertion function equation
        #ghi_column_vector=calc_irrad(dni_vector,dhi_vector,lat,lng,gamma_s,t_z,tilt,soil_shad_loss)

        ghi_column_vector=const['ghi_column_vector']
        
        
        
        Transposed_ghi_vector=ghi_column_vector.transpose() #Transposing the column vector into a row vector 
        
        ghi_matrix=np.reshape(Transposed_ghi_vector,(24,365),order='F')
        #ghi_matrix_pv=ghi_matrix/1000 #convert the GHI into kW/m2
        
        
        
        """================================================Wind speed data====================================================================="""
        #wind_speed=pd.read_csv(PROJECT_DIR + weather_file_name,usecols=[46],skiprows=1,)
        
        #wind_speed_col_vector=wind_speed.as_matrix()
        
        #Transposed_wind_vector=wind_speed_col_vector.transpose() #Transposing the column vector into a row vector 
        
        #wind_matrix=np.reshape(Transposed_wind_vector,(24,365),order='F')
        
        """=================================Dry bulb temperature data========================================================================"""
        
        #temp=pd.read_csv(PROJECT_DIR + weather_file_name,usecols=[31],skiprows=1,)
        
        #temp_col_vector=temp.as_matrix()
        
        #Transposed_temp_vector=temp_col_vector.transpose() #Transposing the column vector into a row vector 
        
        #temp_matrix=np.reshape(Transposed_temp_vector,(24,365),order='F')
        
        #This commented piece of code is for Detroit' electricity price matrix generation 
    # =============================================================================
    # """===================================================================================================================================================================================="""
    # """ Hard Coding of the electrcity rate in Detroit """
    # rate_type_1=[0.0983,0.0983,0.0983,0.0983,0.0983,0.0983,0.0983,0.0983,0.0983,0.0983,0.0983,0.1670,0.1670,0.1670,0.1670,0.1670,0.1670,0.1670,0.1670,0.1670,0.0983,0.0983,0.0983,0.0983]
    # 
    # rate_type_2=[0.1007,0.1007,0.1007,0.1007,0.1007,0.1007,0.1007,0.1007,0.1007,0.1007,0.1007,0.1892,0.1892,0.1892,0.1892,0.1892,0.1892,0.1892,0.1892,0.1892,0.1007,0.1007,0.1007,0.1007]
    # 
    # """ Creation of first matrix"""
    # 
    # 
    # rate_matrix=np.zeros((24,365))
    # 
    # for i in range(152):               # Filling the first part of the matrix 
    #     rate_matrix[:,i]=rate_type_1
    # 
    # for i in range(155):              # Filling the first part of the matrix 
    #     rate_matrix[:,i+152]=rate_type_2
    #     
    # for i in range(60):                 # Filling the first part of the matrix
    #     rate_matrix[:,i+305]=rate_type_1
    # 
    # """======================================================================================================================================================================================"""
    # 
    # =============================================================================
        rate_dataframe=pd.DataFrame(touMatrix)
        monthly_rate_columns=rate_dataframe.as_matrix()
        rate_type_1=monthly_rate_columns[:,0]
        rate_type_2=monthly_rate_columns[:,3]
        rate_type_3=monthly_rate_columns[:,5]
        rate_type_4=monthly_rate_columns[:,6]
        rate_type_5=monthly_rate_columns[:,9]
        rate_matrix=np.zeros((24,365))
        
        for i in range(90):               # Filling the first part of the matrix (January -March)
            rate_matrix[:,i]=rate_type_1
        
        for i in range(61):              # Filling the second part of the matrix  (April-May)
            rate_matrix[:,i+90]=rate_type_2
            
        for i in range(30):                 # Filling the third part of the matrix (June)
            rate_matrix[:,i+151]=rate_type_3
            
        for i in range(92):                 # Filling the fourth part of the matrix (July-September)
            rate_matrix[:,i+181]=rate_type_4
        
        for i in range(92):                 # Filling the first part of the matrix (October-December)
            rate_matrix[:,i+273]=rate_type_5
        """ The price of electricity is increased based on percentage price increment entered by user"""
        
        percent_inc_matrix=np.ones((24,365*year_analysis))
        
        for m in range(year_analysis-1):
            
            percent_inc_matrix[:,((m+1)*365):(m+2)*365]=percent_inc_matrix[:,(m*365):((m+1)*365)]*(1+(percent_inc_in_elec_price/100))
            
                
        rate_matrix_1=np.tile(rate_matrix,year_analysis)
        
        rate_matrix=np.multiply(rate_matrix_1,percent_inc_matrix)
        
        """=========================================================================================================================================================================================== """   
        
        """ Below calculates the PV generation per hour using wind speed, temperature and degrades the value on the basis of entered value"""
    
    
        term1= (np.exp(-0.075*wind_matrix-3.56))*ghi_matrix
        term2=temp_matrix
        
        module_back_temp= term1+term2  #Equation to calculate module back temperature with 
        
        cell_temp=module_back_temp + (ghi_matrix)*3
        
        #Check if the temperature is greater than 25 degrees or not and apply the condition for PV generation equation
    
        #this matrix wiil have  value of 1 if the temperature is less than 25 degree celsius and less than 1 whenever temperature goes more than 25
        matrix_a=np.where(cell_temp<25,1,cell_temp)
        temp_coeff_matrix=np.where(matrix_a>1,(1-((matrix_a-25)*(1-max_power_temp_coeff)/100)),matrix_a)
        
        pv_power_matrix=pv_module_efficiency*pv_panel_area*np.array(ghi_matrix)*temp_coeff_matrix
    

    
        #pv_power_matrix=(pv_module_efficiency*pv_panel_area*np.array(ghi_matrix))*(1-((max_power_temp_coeff/100)*(cell_temp-25)))  #Calculating PV output from GHI (this equation needs to be refined more later on) 
        
        
        pv_power_matrix=np.tile(pv_power_matrix,year_analysis)
        
        percent_dec_matrix=np.ones((24,365*year_analysis))
        
        
        
        pv_power_matrix=np.multiply(pv_power_matrix,percent_dec_matrix)
        
        
        #write something here to introduce ILR 
    
        inverter_cap=arbit_solar_panel_size/ILR
        
        pv_power_matrix=np.where(pv_power_matrix>inverter_cap,inverter_cap,pv_power_matrix)
        
        pv_power_matrix=pv_power_matrix*(invert_eff/100)
            
        # The battery charge matrix here needs to be modified to keep the battery charge consistent from the previous day
        pv_minus_consump=pv_power_matrix-Elec_consumption_matrix

        
        """====This place is reserved for an equation which generates a numpy vector having the  degrading capacity of battery modules based on the equation you derived   """
    
        pv_minus_consump_vector=pv_minus_consump.flatten('F')
        consump_minus_pv_vect=np.negative(pv_minus_consump_vector)
        
        curnt_batt_capac[0]=capacity_of_batt_module
        soc_vect[0]=capacity_of_batt_module                                #These statements intialzie the values of variables to be used in the upcoming code
        thpt_local_1=0
        thpt_global=0
        batt_replc=0
        batt_replc_hour=0 #Counts the values of when the battery gets replaced
        j=0
        k=0
        l=0
        disp_thrpt=0
        
        throuput_check_list=[] #Delete the list after checking the throughput each year 
        
        #This loops run each hour to calculate if the degrading capacity of the battery given by the 
        for i in range(8760*year_analysis-1):
            
            # this if condition checks if 7 weeks have ended and degrades the capcity with calendar ageing equation (every 7 weeks)
            if(k!=0 and k%(24*30)==0):
                                                                    
            
                temp_value=capacity_of_batt_module*(1-alpha_cap*((k/24)**0.75))
                #curnt_batt_capac[i+1]=curnt_batt_capac[i]-(capacity_of_batt_module-temp_value)
                curnt_batt_capac[i+1]=temp_value
                #k=0
                
                if(curnt_batt_capac[i+1]>capacity_of_batt_module):      #Don't allow battery current battery capacity to be more than what we started
                    curnt_batt_capac[i+1]=capacity_of_batt_module
                
                if(curnt_batt_capac[i+1]<(minm_bat_capac*capacity_of_batt_module)):     #Don't allow battery capacity to be smaller than then the lower limit correspnding to user sepcified DOD 
                    curnt_batt_capac[i+1]=(minm_bat_capac*capacity_of_batt_module)
            else:
                curnt_batt_capac[i+1]=curnt_batt_capac[i]
        
            k+=1    
            
            x=soc_vect[i]*(batt_rtrip_eff/100)-consump_minus_pv_vect[i]
            
            #These set of if and else conditions check the amount of the battery filled up by the PV generation (The condiion next to if suggests that PV is more than conusmption)
            
            #These set of if and else conditions check the amount of the battery filled up by the PV generation (The condiion next to if suggests that PV is more than conusmption)
        
            if(consump_minus_pv_vect[i]<0):                                                      
                #Check if the battery is already filled upto its total capacity
                if(x>curnt_batt_capac[i]):                                                              
                    soc_vect[i+1]=curnt_batt_capac[i]
                    thpt_local=0
                    #No buying from grid so don't chnage the default zero value of the numpy matrix
                    
                else:
                    #Battery gets charged with x amount and the same amount is taken away from the surplus matrix (Excaluding the battery losses)
                    soc_vect[i+1]=soc_vect[i]+x*(batt_rtrip_eff/100)
                    #waste the PV if it is more than what you need to 
                    if(soc_vect[i+1]>curnt_batt_capac[i]):
                        soc_vect[i+1]=curnt_batt_capac[i]
                    
                    thpt_local=0
                    consump_minus_pv_vect[i]=consump_minus_pv_vect[i]-x
                    
            #This else statement deals with different subconditions when Consumption is more than PV generation
            else:
                
                thpt_indicator=(soc_vect[i]*(batt_rtrip_eff/100))-consump_minus_pv_vect[i]-(minm_bat_capac*capacity_of_batt_module)
                
                #This if condition shows battery has enough to supply the Consumption more than the PV generation
                if(thpt_indicator>0):
                    buy_elec[i]=0
                    soc_vect[i+1]=(soc_vect[i]*(batt_rtrip_eff/100))-consump_minus_pv_vect[i]
                    thpt_local=consump_minus_pv_vect[i]
                    #No buying from grid so don't chnage the default zero value of the numpy matrix
                
                #This condtion gets actiavted when the battery charge is not enough to satisfy the consumption over PV generation and we have to but from grid
                else:
                    #Partial usin battery partially buying from grid
                    if(soc_vect[i]*(batt_rtrip_eff/100)>(minm_bat_capac*capacity_of_batt_module)):
                        thpt_local=soc_vect[i]-(minm_bat_capac*capacity_of_batt_module)
                        thpt_recvd=(soc_vect[i]*(batt_rtrip_eff/100))-(minm_bat_capac*capacity_of_batt_module)
                        buy_elec[i]=consump_minus_pv_vect[i]-thpt_recvd
                        
                        #Making sure that we don not buy from the grid in excess of the hourly limit for Fast or Home Charging options
                        if(buy_elec[i]>max_bought_elec_grid):
                            buy_elec[i]=max_bought_elec_grid
                        
                        
                        soc_vect[i+1]=(minm_bat_capac*capacity_of_batt_module)
                    #Nothing left in the battery buy everything from the grid
                    else:
                        thpt_local=0
                        buy_elec[i]=consump_minus_pv_vect[i]
                        
                        #Making sure that we don not buy from the grid in excess of the hourly limit for Fast or Home Charging options
                        if(buy_elec[i]>max_bought_elec_grid):
                            buy_elec[i]=max_bought_elec_grid
                        
                        
                        soc_vect[i+1]=(minm_bat_capac*capacity_of_batt_module)
                        
                        
                        
            throuput_check_list.append(thpt_local)
            
            thpt_local_1=thpt_local_1+thpt_local
            
            if(l!=0 and l%(24*30)==0):  #cyclic ageing accounted for every 3 weeks 
                thpt_each_string=(thpt_local_1/capacity_of_batt_module)*string_capacity
                new_strng_capac=string_capacity*(1-beta_cap*((thpt_each_string/voltage)**(1/2)))
                temp_value_1=(new_strng_capac/string_capacity)*capacity_of_batt_module
                #curnt_batt_capac[i+1]=curnt_batt_capac[i+1]-(capacity_of_batt_module-temp_value_1)
                curnt_batt_capac[i+1]=curnt_batt_capac[i+1]-(capacity_of_batt_module-temp_value_1)
                #l=0
                
        
                
                
                #thpt_local_1=0
                
                if(curnt_batt_capac[i+1]<(minm_bat_capac*capacity_of_batt_module)):     #Don't allow battery capacity to be smaller than then the lower limit correspnding to user sepcified DOD 
                    curnt_batt_capac[i+1]=(minm_bat_capac*capacity_of_batt_module)
                
            else:
                curnt_batt_capac[i+1]=curnt_batt_capac[i]
            
            l+=1
            
            thpt_global=thpt_global+thpt_local
            
            replaced=0 #Define a variable that would become 1 if the maximum throughput or minimum battery capacity is reached before 5 years and the battery is replaced already
            
            if(thpt_global>throughput_limit*capacity_of_batt_module):      #This condition checks if throuput limit has reached and it is time to change the battery
                curnt_batt_capac[i+1]=capacity_of_batt_module
                batt_replc+=1
                batt_replc_hour=i
                thpt_global=0
                thpt_local_1=0
                k=0
                l=0
                replaced=1
            
            if(curnt_batt_capac[i]==(minm_bat_capac*capacity_of_batt_module)): #Check if you have exhausted battey capacity beyond a certain value (20% in our case)
                curnt_batt_capac[i+1]=capacity_of_batt_module
                batt_replc+=1
                batt_replc_hour=i
                k=0
                l=0
                thpt_global=0
                thpt_local_1=0
                replaced=1
        
        
        
            
            j+=1

            #Check if the used speciied years have passed for Battery replacement
            if(j>(batt_rplcmt_year*8760) and replaced==0):
                curnt_batt_capac[i+1]=capacity_of_batt_module
                batt_replc+=1
                batt_replc_hour=i
                thpt_global=0
                thpt_local_1=0
                k=0
                l=0
                j=0
        
    
            
            soc_check=soc_vect[i]
                
            
        
            
            disp_thrpt=disp_thrpt+thpt_local
            #Test code for checking battery throughput each year
        # =============================================================================
        #     if(i!=0 and i%8760==0):
        #         throuput_this_year.append(disp_thrpt)
        #     
        # =============================================================================
            
            
            
            
            thpt_local=0
            
        final_soc_matrix=soc_vect.reshape((24,365*year_analysis),order='F')  # This is the final matrix which needs to be compared with battery charge matrix
        
        
        final_soc_matrix_1=final_soc_matrix       
        
    
        elec_bought_grid=buy_elec.clip(0)
        
        
        elec_bought_grid=np.reshape(elec_bought_grid,(24,365*year_analysis),order='F')
        
        """=======The variable in this module will be added to final cost function only if the battery is assumed to be charged from the grid======================================================================================================================================================================"""
        
            
        #cost_matrix_for_battery_charging=battery_charge_matrix.dot(rate_matrix)
        
        # =============================================================================
        #     cost_of_elec_for_batt_charging=np.multiply(battery_charge_matrix,rate_matrix)  #multiply each element of one matrix with another 
        #     
        #     daily_cost_of_battery_charging=np.sum(cost_of_elec_for_batt_charging,axis=0)  # a 365 by 1 vector containing the daily cost of the battery as each element
        # =============================================================================
        
        
        
        """The below piece of code tries to see when there is an increase in the battery charge (That is the point where electricity has been bought to charge the battery )
        ======================================================================================================================================================"""
        
        #final_soc_matrix_1=final_soc_matrix #Assigning final state of charge matrix values to another matrix since we will need the final_SOC_matrix 
        
        final_soc_matrix_1_vector_form=final_soc_matrix_1.flatten('F')
        
        """The below code finds out the places where the state of charge has increased and stores the increase in value of 
        ================================================================================================================================================"""
        
        
        indices_where_battery_charge_inc=[t-s for s,t in zip(final_soc_matrix_1_vector_form,final_soc_matrix_1_vector_form[1:])]
        indices_where_battery_charge_inc=[0 if i<0 else i for i in indices_where_battery_charge_inc]
            
        hours_when_batt_charg= [0] + indices_where_battery_charge_inc    
        
        amount_batt_charges=np.reshape(hours_when_batt_charg,(24,365*year_analysis),order='F') #Variable might be needed in future, not right now though
        
        
        """====================================Net metering function=========================================================================="""
        
        total_net_met_benf=np.zeros((24,365*year_analysis))
        total_feed_in_tarff_benf=np.zeros((24,365*year_analysis))
        pv_minus_consump_vector=np.negative(consump_minus_pv_vect)
        pv_minus_consump_temp=pv_minus_consump_vector
        pv_minus_consump_temp_1=pv_minus_consump_temp-hours_when_batt_charg
        pv_minus_consump=np.reshape(pv_minus_consump_temp_1,(24,365*year_analysis),order='F')
        pv_minus_consump[pv_minus_consump<0]=0 
        


        a=[31,59,90,120,151,181,212,243,273,304,334,365] #Write a more genral script here to generate this list based on user (Or maybe just put number of months for 10 years)
        
        days_list_year=np.array(a)
        
        for z in range(year_analysis-1):
        
            t=days_list_year+ 365*(z+1)
            days_list=np.append(a,t)
            a=days_list      # this list has the number of days in respective months  (For battery degradation to work we will haev to take 5 years into account)
        
        days_list_final=np.insert(days_list,0,0)            # number of days in each month of a year        
        #delete these lists after debuging after debugging the net metering code
        net_met_list=[]
        monthly_PV_list=[]
        monthly_consump_list=[]
        monthly_pv_list_without_red=[]

        for i in range (0, (len(days_list)-1)):
         
        
            """=====================The below section slices of PV surplus, electricity conusmptio and rate_matrix for the current month=========="""    
            
            pv_surplus_month=pv_minus_consump[:,days_list_final[i]:days_list_final[i+1]]
            monthly_pv=np.sum(pv_surplus_month)
            
            monthly_pv_list_without_red.append(monthly_pv) #Remove after testing
            
            
            
            elec_conump_month=elec_bought_grid[:,days_list_final[i]:days_list_final[i+1]]
            monthly_consmp=np.sum(elec_conump_month)
            monthly_consump_list.append(monthly_consmp)
            
            month_rate_matrix=rate_matrix[:,days_list_final[i]:days_list_final[i+1]] 
            
            
            #Check if user wants net metering 
            if(net_metering==1):
                
                if (np.sum(pv_surplus_month)>0):
             
                
                    wt_avg=monthly_consmp/monthly_pv
                    pv_surplus_month_1=np.where(pv_surplus_month>0,wt_avg*pv_surplus_month,pv_surplus_month)
                    pv_surplus_after_correction=np.sum(pv_surplus_month_1) #Delete after testing 
                    
                    monthly_PV_list.append(pv_surplus_after_correction) #Delete after testing
                    
                    
                    net_met_benf=np.multiply(pv_surplus_month_1,month_rate_matrix)
                    
                    """==== Calculation of corresponding feed in tariff benefit (if there were are entering the else part of the statement)================="""
                        
                    
                    
                        
                else:
                    net_met_benf=pv_surplus_month*0
                
                total_net_met_benf[:,days_list_final[i]:days_list_final[i+1]]=net_met_benf
            
            #No need to supply a condition for non use of net-metering as total_net_met_benf is already a zeros numpy matrix of requisite size
        
            
            if(feed_in_tariff==1):
                
                feed_in_tariff_pv= pv_surplus_month   #PV for feed-in tariff per month
                feed_in_tariff_pv[feed_in_tariff_pv<0]=0 
                feed_in_tarff_savings=feed_in_tariff_pv*feed_in_tariff_rate 
                total_feed_in_tarff_benf[:,days_list_final[i]:days_list_final[i+1]]=feed_in_tarff_savings
                
            #print("The net metering benefit thi month is:" ,np.sum(total_net_met_benf))
                
            #No need to supply a condition for non use of feed-in tariff as total_feed_in_tarff_benf is already a zeros numpy matrix of requisite size
        

        """Cost functions===================================================================================================================
        ========================================================================================================================================"""
        
        """Cost of buying electricity for each hour throughout the year"""
        cost_of_buy_elec=np.multiply(elec_bought_grid,rate_matrix)     
        
        
        """Cost of electricity to charge the battery"""
        
    # =============================================================================
    #     cost_of_elec_charg_batt=np.multiply(amount_batt_charges,rate_matrix)   #REMOVE this if you don't want battery to be charged from grid  
    # =============================================================================
        """ Cost of the battery per hour """
    
    
        batt_cost=(capacity_of_batt_module*cost_of_batt_module_per_kWh)
        """ Cost of the solar panel  """
    
        pv_cost=(cost_of_solar_panel*arbit_solar_panel_size)
        
        inverter_cost=inverter_ccost_per_kw*inverter_cap
        
        """Defining cost of the battery per hour """
        
        #rho=((capacity_of_batt_module*cost_of_batt_module_per_kWh + cost_of_batt_accesory)/(365*batt_warant_time))/24  #Dividing the whole function by 24 so that we can have   
        
        """ Cost of the solar panel per hour """
        #psi=((cost_of_solar_panel*arbit_solar_panel_size+cost_of_solar_panel_accesory)/(365*solar_panel_waranty))/24
        
        # Defining a matrix whihc holds the values of the cost_of_microgrid for each day
        
        #fixed_cost=psi+rho  # We still need to add the base fee for service connection (maybe doing it per hour for a year would work)
        
        #npv,pv_salv,batt_salv,inv_salv=calc_npv(year_analysis,pv_cost,inverter_cost,batt_cost,batt_replc_hour,base_fee_conec_cost,batt_replc,sales_tax_perc,liab_insu_fee,one_time_conec_fee,pv_onm,batt_onm,invrtr_onm,cost_of_buy_elec,total_net_met_benf,total_feed_in_tarff_benf,discnt_rate,infl_rate,pv_lifetime,invrtr_lifetime)
        
        #gwp_impact,ced_impact=calc_env_impact(year_analysis,arbit_solar_panel_size,pv_lifetime,invrtr_lifetime,capacity_of_batt_module,batt_replc,batt_replc_hour,batt_rplcmt_year,ILR,elec_bought_grid,total_net_met_benf,rate_matrix,total_feed_in_tarff_benf,feed_in_tariff_rate,PV_GWP,PV_CED,Batt_GWP,Batt_CED,Inv_GWP,Inv_CED,Elec_GWP,Elec_CED)
            
        #AC,LCOE=calc_cost(real_discnt,year_analysis,npv,Elec_consumption_matrix)
        
        #cash_flow_elec,cash_flow_NM,cash_flow_FIT,cash_flow_liab,cash_flow_onm,cash_flow_comp=calc_cashflow(pv_cost,batt_cost,inverter_cost,batt_replc_hour,batt_replc,year_analysis,pv_onm,batt_onm,invrtr_onm,base_fee_conec_cost,sales_tax_perc,liab_insu_fee,pv_salv,batt_salv,inv_salv,cost_of_buy_elec,total_net_met_benf,total_feed_in_tarff_benf)
        
        npv,pv_salv,batt_salv,inv_salv=calc_npv(year_analysis,pv_cost,inverter_cost,batt_cost,batt_replc_hour,base_fee_conec_cost,batt_replc,sales_tax_perc,liab_insu_fee,one_time_conec_fee,pv_onm,batt_onm,invrtr_onm,cost_of_buy_elec,total_net_met_benf,total_feed_in_tarff_benf,discnt_rate,infl_rate,pv_lifetime,invrtr_lifetime,arbit_solar_panel_size,capacity_of_batt_module,inverter_cap)
    
        gwp_impact,ced_impact=calc_env_impact(year_analysis,arbit_solar_panel_size,pv_lifetime,invrtr_lifetime,capacity_of_batt_module,batt_replc,batt_replc_hour,batt_rplcmt_year,ILR,elec_bought_grid,total_net_met_benf,rate_matrix,total_feed_in_tarff_benf,feed_in_tariff_rate,PV_GWP,PV_CED,Batt_GWP,Batt_CED,Inv_GWP,Inv_CED,Elec_GWP,Elec_CED)
        
        AC,LCOE=calc_cost(real_discnt,year_analysis,npv,Elec_consumption_matrix)
    
        cash_flow_elec,cash_flow_NM,cash_flow_FIT,cash_flow_liab,cash_flow_onm,cash_flow_comp=calc_cashflow(pv_cost,batt_cost,inverter_cost,batt_replc_hour,batt_replc,year_analysis,pv_onm,batt_onm,invrtr_onm,base_fee_conec_cost,sales_tax_perc,liab_insu_fee,pv_salv,batt_salv,inv_salv,cost_of_buy_elec,total_net_met_benf,total_feed_in_tarff_benf,arbit_solar_panel_size,capacity_of_batt_module,inverter_cap)

        #cost_of_microgrid_per_hour=np.add(fixed_cost,cost_of_buy_elec-total_net_met_benf-total_feed_in_tarff_benf)
        
        base_AC,base_LCOE,base_GWP,base_CED=baseline(year_analysis,discnt_rate,infl_rate,sales_tax_perc,base_fee_conec_cost,one_time_conec_fee,Elec_consumption_matrix,rate_matrix,Elec_GWP,Elec_CED)

        if (carbn_ftprnt==1):
            obj=gwp_impact
        elif (cum_dem==1):
            obj=ced_impact
        else:
            obj=npv
        
        #elec_bought_grid_sum = np.sum(elec_bought_grid)
            
        data = {"final_soc_matrix" : final_soc_matrix, # Chek with earlier codes and figuer out the indentation problem here 
                "total_net_met_benf" : total_net_met_benf,
                "elec_bought_grid":elec_bought_grid,
                "year_analysis":year_analysis,
                "AC":AC,
                "LCOE":LCOE,
                "cash_flow_FIT":cash_flow_FIT,
                "cash_flow_NM":cash_flow_NM,
                "cash_flow_elec":cash_flow_elec,
                "cash_flow_comp":cash_flow_comp,
                "cash_flow_liab":cash_flow_liab,
                "cash_flow_onm":cash_flow_onm,
                "curnt_batt_capac":curnt_batt_capac,
                "gwp_impact":gwp_impact,
                "ced_impact":ced_impact,
                "disp_thrpt":disp_thrpt,
                'inverter_cap': inverter_cap,
                "base_AC":base_AC,
                "base_LCOE":base_LCOE,
                "base_GWP":base_GWP,
                "base_CED":base_CED,
                "year_analysis":year_analysis,
                "percent_dec_matrix":percent_dec_matrix} 
        
        return obj, data, pv_power_matrix, Elec_consumption_matrix

    class MyProblem(Problem):
        def __init__(self,const):
            super().__init__(n_var=2, n_obj=1, n_constr=0,
                            xl=np.array([pv_lower_limit,bat_lower_limit]), xu=np.array([pv_upper_limit,bat_upper_limit]))
            self.const = const
        def _evaluate(self, x, out, *args, **kwargs):
            
            F = np.full((len(x), 1), np.nan)
            
            for k, _x in enumerate(x): 
                    F[k, 0], _, _, _ = evaluate(_x, self.const)  # Number of dashes equivalent to number of variables you wanna show
                
                    
            out["F"] = F

    # ***** MAIN FUNCTION *****
    warnings.filterwarnings("ignore")
    problem = MyProblem(const)
    
    ga = GA(pop_size=10,eliminate_duplicates=True)
    #ga = NelderMead()
    #de = de(pop_size=20,eliminate_duplicates=True)

    res = minimize(problem,
                ga , # change the algorihtm here. either de or ga
                termination=('n_gen', calc_amount),
    # =============================================================================
    #                termination=NelderAndMeadTermination(xtol=1e-6,
    #                  ftol=1e-6,
    #                  n_max_iter=1e6,
    #                  n_max_evals=60),
    # =============================================================================
                seed=1,
                save_history=True,
                verbose=True)

    print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))
    _, data, pv_power_matrix, Elec_consumption_matrix = evaluate(res.X, const)

    final_soc_matrix = data['final_soc_matrix']
    total_net_met_benf=data['total_net_met_benf']
    elec_bought_grid=data['elec_bought_grid']
    year_analysis=data['year_analysis']
    percent_dec_matrix=data['percent_dec_matrix']
    AC=data['AC']
    LCOE=data['LCOE']
    cash_flow_FIT=data['cash_flow_FIT']
    cash_flow_NM=data['cash_flow_NM']
    cash_flow_elec=data['cash_flow_elec']
    cash_flow_comp=data['cash_flow_comp']
    cash_flow_liab=data['cash_flow_liab']
    cash_flow_onm=data['cash_flow_onm']
    curnt_batt_capac=data['curnt_batt_capac']
    gwp_impact=data['gwp_impact']
    ced_impact=data['ced_impact']
    disp_thrpt=data['disp_thrpt']
    inverter_cap=data['inverter_cap']
    base_AC=data['base_AC']
    base_LCOE=data['base_LCOE']
    base_GWP=data['base_GWP']
    base_CED=data['base_CED']

    #gwp=(res.X[0]*(1853.6463/30)*year_analysis)+(res.X[0]*(81.011096/30)*year_analysis)+(res.X[1]*16.0962)+(np.sum(elec_bought_grid)*0.569058)             #For now, the size of inveter is assumed same as the size of PV and the average of US values have been assumed

    #ced=(res.X[0]*(30618.38967/30)*year_analysis)+(res.X[0]*(1263.69076/30)*year_analysis)+(res.X[1]*268.0425)+(np.sum(elec_bought_grid)*11.50187)

    #print(total_net_met_benf.sum())

    #***** CUSTOM MATRIX OUTPUT *****
    n_1=25
    a=np.diff(final_soc_matrix[:,n_1])                     
    throughput=np.abs(((a<0)*a).sum())

    grid = []
    capital_cost = []
    operation_main = []

    for i in range(len(cash_flow_FIT[0])):
        grid.append(round((cash_flow_FIT[0][i] + cash_flow_NM[0][i] + cash_flow_elec[0][i]),2))
        capital_cost.append(round(cash_flow_comp[0][i],2))
        operation_main.append(round((cash_flow_liab[0][i] + cash_flow_onm[0][i]),2))

    
    #buf = BytesIO()
    #fig, ax = plt.subplots(figsize=(12, 4))

    #ax.bar(np.arange(year_analysis+1), grid, label="Grid")
    #ax.bar(np.arange(year_analysis+1), capital_cost, label="Capital Costs")
    #ax.bar(np.arange(year_analysis+1), operation_main, label="Operation and Maintenance")

    #ax.set_ylabel('Dollars ($)', size=20)
    #ax.set_xlabel('Year', size=20)
    #plt.legend(bbox_to_anchor=(0,1.02,1,0.2), loc="lower left", ncol=3, mode="expand")

    #plt.tight_layout()
    #fig.savefig(buf, format='png')
    #matrix_bar_chart = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
    #buf.close()

    xticks = np.asarray([0,1,2,3,4,5])
    yticks = np.asarray([0,4,8,12,16,20,24])
    
    xticks_month_str = np.asarray(['Mar', 'Jun', 'Sep', 'Dec', 'Mar', 'Jun', 'Sep', 'Dec', 'Mar', 'Jun', 'Sep', 'Dec', 'Mar', 'Jun', 'Sep', 'Dec', 'Mar', 'Jun', 'Sep', 'Dec'])
    xticks_month = np.asarray([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19])

    buf = BytesIO()
    fig, ax = plt.subplots(figsize=(12, 4))
    ax = sns.heatmap(final_soc_matrix, xticklabels=xticks, yticklabels=yticks, cmap="YlGnBu")
    ax.set_xticks(xticks*ax.get_xlim()[1]/5)
    ax.set_yticks(yticks*ax.get_ylim()[1]*2)
    plt.xlabel('Year')
    plt.ylabel('Hours')
    plt.xticks(rotation=0)
    plt.yticks(rotation=0)
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(xticks_month*ax2.get_xlim()[1]/20 + 45)
    ax2.set_xticklabels(xticks_month_str)
    ax2.set_xlabel('Month')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    plt.tight_layout()
    fig.savefig(buf, format='png')
    matrix_stateOfCharge = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
    buf.close()

    buf = BytesIO()
    fig, ax = plt.subplots(figsize=(12, 4))
    ax = sns.heatmap(pv_power_matrix, xticklabels=xticks, yticklabels=yticks, cmap="YlGnBu")
    ax.set_xticks(xticks*ax.get_xlim()[1]/5)
    ax.set_yticks(yticks*ax.get_ylim()[1]*2)
    plt.xlabel('Year')
    plt.ylabel('Hours')
    plt.xticks(rotation=0)
    plt.yticks(rotation=0)
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(xticks_month*ax2.get_xlim()[1]/20 + 45)
    ax2.set_xticklabels(xticks_month_str)
    ax2.set_xlabel('Month')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    plt.tight_layout()
    fig.savefig(buf, format='png')
    matrix_pv_power = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
    buf.close()
    

    buf = BytesIO()
    fig, ax = plt.subplots(figsize=(12, 4))
    ax = sns.heatmap(Elec_consumption_matrix, xticklabels=xticks, yticklabels=yticks, cmap="YlGnBu")
    ax.set_xticks(xticks*ax.get_xlim()[1]/5)
    ax.set_yticks(yticks*ax.get_ylim()[1]*2)
    plt.xlabel('Year')
    plt.ylabel('Hours')
    plt.xticks(rotation=0)
    plt.yticks(rotation=0)
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(xticks_month*ax2.get_xlim()[1]/20 + 45)
    ax2.set_xticklabels(xticks_month_str)
    ax2.set_xlabel('Month')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    plt.tight_layout()
    fig.savefig(buf, format='png')
    matrix_elec_consumption = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
    buf.close()  

    #---------------------------------------------------------------------------------------------#
    # Labor
    #---------------------------------------------------------------------------------------------
    global bptk
    
    print()
    print("Available Scenario Managers and Scenarios:")
    print()
    managers = bptk.scenario_manager_factory.get_scenario_managers(scenario_managers_to_filter=[])
    
    for key, manager in managers.items():
        print("")
        print("*** {} ***".format(key))

        for name in manager.get_scenario_names():
            print("\t {}".format(name))
    
    scenario_manager_labor={
        "smTemp":
            {
            "source":"static/slb/labor/simulation_models/SLBremanlabor.stmx",
            "model":"static/slb/labor/simulation_models/SLBremanlabor"
            }
    }

    scenario_manager_elec={
        "smTemp":
            {
            "source":"static/slb/electricity/simulation_models/SLBremanelectricity.stmx",
            "model":"static/slb/electricity/simulation_models/SLBremanelectricity"
            }
    }

    scenario_manager_trans={
        "smTemp":
            {
            "source":"static/slb/transportation/simulation_models/SLBreman3.stmx",
            "model":"static/slb/transportation/simulation_models/SLBreman3"
            }
    }

    scenario_manager_eol={
        "smTemp":
            {
            "source":"static/slb/EOLvalue/simulation_models/EOLvalue.stmx",
            "model":"static/slb/EOLvalue/simulation_models/EOLvalue"
            }
    }

    scenario_name ="UserInput"

    constants = {
        "startYearForReman": 2020, #Year to start remanufacturing
        "yearOfSwitchFromEaToGp": 2028, #Year to switch to general public
        "updfEa": 0.62, #Used product discount factor (Early adopter)
        "updfGp": 0.59, #Used product discount factor (General public)
        "ppEa": 0.37, #Public perception of SLBs (Early adopter)
        "ppGp": 0.44, #Public perception of SLBs (General public)
        "technicallyFeasibleBatteriesFraction": 0.95, #Technically feasible end-of-life batteries
        "valueOfThroughputOldBattery":0.8, #Value of SLB throughput
        "allowableProfit%":0.01, #Allowable profit

        "costOfRemanCapacity": 11.35,  #Equipment and facility cost 
        "electricityPerKwh": 7.5, #Electricity used (kWh/kWh SLB)
        "costOfElectricity":0.0688, #Electricity cost ($/kWh)
        "transporationCostPerMile": 1.891, #Transportation cost ($/mile)
        "tonneMilesTransportedMin": 526.8, #Transportation distance (ton-mile)
        "numberOfHoursPerYearPerLaborer":2016, #Labor hours (h/year)
        "outputPerHour": 3, #Output per hour 
        "laborInFacility": 10, #Number of laborers per 3 shift (no)
        "costOfLaborPerHour": 20.67, #Labor cost ($/h)
        "recyclingValue": -4.1 #Recycling value ($/kWh)
    }

    # Get the input values to constants(dictionary)
    output_model = request.POST['ouput-model']
    constants["startYearForReman"] = int(request.POST['year-start-remanufact'])
    constants["yearOfSwitchFromEaToGp"] = float(request.POST['year-switch-general'])
    constants["updfEa"] = float(request.POST['used-product-dis-fact-early']) / 100
    constants["updfGp"] = float(request.POST['used-product-dis-fact-general']) / 100
    constants["ppEa"] = float(request.POST['perception-early']) / 100
    constants["ppGp"] = float(request.POST['perception-general']) / 100
    constants["technicallyFeasibleBatteriesFraction"] = float(request.POST['tech-feasible-eol-bat']) / 100
    constants["valueOfThroughputOldBattery"] = float(request.POST['val-slb']) / 100
    constants["allowableProfit%"] = float(request.POST['allow-profit']) / 100

    constants["costOfRemanCapacity"] = float(request.POST['equip-fac-cost'])
    constants["electricityPerKwh"] = float(request.POST['elec-used'])
    constants["costOfElectricity"] = float(request.POST['elect-cost'])
    constants["transporationCostPerMile"] = float(request.POST['trans-cost'])
    constants["tonneMilesTransportedMin"] = float(request.POST['trans-distance'])
    constants["numberOfHoursPerYearPerLaborer"] = int(request.POST['labor-hours'])
    constants["outputPerHour"] = int(request.POST['output-per-hour'])
    constants["laborInFacility"] = int(request.POST['num-labor-shift'])
    constants["costOfLaborPerHour"] = float(request.POST['labor-cost'])
    constants["recyclingValue"] = float(request.POST['recycle-value'])

    # dictionary delete / clean speicifc key depending on option
    if output_model == "pot-labor-cost":
        constants.pop('costOfLaborPerHour',None)
    elif output_model == "pot-elect-cost":
        constants.pop('costOfElectricity',None)
    elif output_model == "pot-trans-distance":
        constants.pop('tonneMilesTransportedMin',None)
    else:
        constants.pop('recyclingValue',None)

    scenario_dictionary ={
        scenario_name:{
            "constants" : constants
        }
    }   

    if output_model == "pot-labor-cost":
        bptk.register_scenario_manager(scenario_manager_labor)
        bptk.register_scenarios(scenario_manager="smTemp",scenarios=scenario_dictionary)

        df_second = bptk.plot_scenarios(
            scenario_managers=["smTemp"],
            scenarios=["UserInput"],
            equations=['costOfLaborPerHourPossible'],
            return_df=True
        )
    elif output_model == "pot-elect-cost":
        bptk.register_scenario_manager(scenario_manager_elec)
        bptk.register_scenarios(scenario_manager="smTemp",scenarios=scenario_dictionary)

        df_second = bptk.plot_scenarios(
            scenario_managers=["smTemp"],
            scenarios=["UserInput"],
            equations=['costOfElectricity'],
            return_df=True
        )
    elif output_model == "pot-trans-distance":
        bptk.register_scenario_manager(scenario_manager_trans)
        bptk.register_scenarios(scenario_manager="smTemp",scenarios=scenario_dictionary)

        df_second = bptk.plot_scenarios(
            scenario_managers=["smTemp"],
            scenarios=["UserInput"],
            equations=['transportDistancePossible'],
            return_df=True
        )
    else:
        bptk.register_scenario_manager(scenario_manager_eol)
        bptk.register_scenarios(scenario_manager="smTemp",scenarios=scenario_dictionary)

        df_second = bptk.plot_scenarios(
            scenario_managers=["smTemp"],
            scenarios=["UserInput"],
            equations=['recyclingValue','eolValueFromRemanufacturing','totalEolValue'],
            return_df=True
        )

    # table 
    df=bptk.plot_scenarios(
        scenario_managers=["smTemp"],
        scenarios=["UserInput"],
        equations=['sellingPriceOfSlb'],
        return_df=True
    )


    buf = BytesIO()
    fig, (ax1, ax2) = plt.subplots(1,2)
    ax1.plot(df[2020:2050])
    ax1.set(xlabel='Year', ylabel='Selling Price Of Slb in $/kWh')
    ax1.set_ylim(0,100)
    ax2.plot(df_second[2020:2050])

    if output_model == "pot-labor-cost":
        ax2.set(xlabel='Year', ylabel='Cost Of Labor in $/hour')
    elif output_model == "pot-elect-cost":
        ax2.set(xlabel='Year',ylabel='CostOfElectricity in $/kWh')
    elif output_model == "pot-trans-distance":
        ax2.set(xlabel='Year',ylabel='Transport Distance in miles')
    else:
        ax2.set(xlabel='Year',ylabel='Total EOL Value in $/year')

    fig.savefig(buf,format='png')
    temp_matrix = base64.b64encode(buf.getvalue()).decode('utf-8').replace('\n', '')
    buf.close()

    return render(request, 'result.html', {
        'zipcode': _zipcode,
        'state': _state,
        'proj_lifetime': _proj_lifetime,
        'year': _year,
        'system_app': _system_app,
        'conn_fee': _conn_fee,
        'elec_price_change': _elec_price_change,
        'feed_in_tariff_rate': _feed_in_tariff_rate,
        'feed_in_tariff': _feed_in_tariff,
        'net_metering': _net_metering,
        'PV_cost': _pv_cost,
        'PV_effi': _pv_effi,
        'inv_cost': _inv_cost,
        'inv_effi': _inv_effi,
        'bat_cost': _bat_cost,
        'bat_effi': _bat_effi,
        'bat_warranty': _bat_warranty,
        'PV_capacity': round(res.X[0], 2),
        'bat_capacity': round(res.X[1], 2),
        'cost': round(res.F[0], 2),
        'matrix_stateOfCharge': matrix_stateOfCharge,
        'matrix_pv_power': matrix_pv_power,
        'matrix_elec_consumption': matrix_elec_consumption,
        'elec_bought_grid': elec_bought_grid,
        'elec_bought_grid_sum': round(np.sum(np.sum(elec_bought_grid)),2),
        'gwp': round(gwp_impact, 2),
        'ced': round(ced_impact, 2),
        'disp_thrpt': round(disp_thrpt[0], 2),
        'county_name': county_name,
        'climate_zone_code' : climate_zone,
        'e_grid_code' : e_grid_code,
        'inverter_cap' : round(inverter_cap,2),
        'temp_matrix': temp_matrix,
        "grid":grid,
        "capital_cost":capital_cost,
        "operation_main": operation_main,
        "year_analysis":year_analysis,
        'base_AC': round(base_AC,2),
        'base_LCOE': round(base_LCOE,2),
        'base_GWP': round(base_GWP,2),
        'base_CED': round(base_CED,2)
    })

def apitest(request):
    zipcode = 48823

    LOCATION_API_KEY = os.getenv('LOCATION_API_KEY')
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    UTILITY_API_KEY = os.getenv('UTILITY_API_KEY')
    
    response_zipcode = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?address={zipcode}&key={LOCATION_API_KEY}')
    location_data = response_zipcode.json()
    lat = round(location_data["results"][0]["geometry"]["location"]["lat"], 6)
    lon = round(location_data["results"][0]["geometry"]["location"]["lng"], 6)
    
    response_weather = requests.get(f"https://developer.nrel.gov/api/solar/nsrdb_data_query.json?api_key={WEATHER_API_KEY}&lat={lat}&lon={lon}")
    weather_data = response_weather.json()
    weather_outputs = weather_data["outputs"]
    weather_urls = []
    # for i in range(len(weather_outputs)):
    #     link = weather_outputs[i]["links"]
    #     weather_urls.append(link)
    for i in range(len(weather_outputs)):
        link = weather_outputs[i]["links"][0]["link"].replace("yourapikey", WEATHER_API_KEY)
        weather_urls.append(link)

    response_utility = requests.get(f"https://api.openei.org/utility_rates?version=3&format=json&api_key={UTILITY_API_KEY}&lat={lat}&lon={lon}&sector=Residential&co_limit=1&approved=true")
    utility_data = response_utility.json()
    utility_data = utility_data["items"]
    utility_checkpoint = []
    for i in range(len(utility_data)):
        cp = (utility_data[i]["name"], utility_data[i]["uri"])
        utility_checkpoint.append(cp)

    return render(request, 'apitest.html', {
        'zipcode': zipcode,
        'location': location_data,
        'weather': weather_urls,
        'utility_checkpoint': utility_checkpoint,
        'location': location_data,
        'lat': lat,
        'lon': lon
    })

def resulttest(request):
    return render(request, 'resulttest.html')

def comparison(request):
    return render(request, 'comparison.html')

def compare(request):
    return render(request, 'result_compare.html')
