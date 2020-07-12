
#      _                   _ _
#  _____| |__ ___ _ __  _ __(_| |___ _ _
# (_-/ _` / _/ _ | '  \| '_ | | / -_| '_|
# /__\__,_\__\___|_|_|_| .__|_|_\___|_|
#                      |_|
# Copyright (c) 2013-2020 transentis management & consulting. All rights reserved.
#
    
import numpy as np
from scipy.interpolate import interp1d
from scipy.special import gammaln
from scipy.stats import norm
import math, statistics, random, logging
from datetime import datetime
import re
import itertools
from copy import copy, deepcopy



def cartesian_product(listoflists):
    """
    Helper for Cartesian product
    :param listoflists:
    :return:
    """
    if len(listoflists) == 1:
        return listoflists[0]
    res = list(itertools.product(*listoflists))

    if len(res) == 1:
        return res[0]

    return res

def LERP(x,points):
    """
    Linear interpolation between a set of points
    :param x: x to obtain y for
    :param points: List of tuples containing the graphical function's points [(x,y),(x,y) ... ]
    :return: y value for x obtained using linear interpolation
    """
    x_vals = np.array([ x[0] for x in points])
    y_vals = np.array([x[1] for x in points])

    if x<= x_vals[0]:
        return y_vals[0]

    if x >= x_vals[len(x_vals)-1]:
        return y_vals[len(x_vals)-1]

    f = interp1d(x_vals, y_vals)
    return float(f(x))

class simulation_model():
    def __init__(self):
        # Simulation Buildins
        self.dt = 1.0
        self.starttime = 2017
        self.stoptime = 2050
        self.units = 'Months'
        self.method = 'Euler'
        self.equations = {

        # Stocks
        
    
        'bevStock'          : lambda t: ( (max([0 , 3.57392])) if ( t  <=  self.starttime ) else (self.memoize('bevStock',t-self.dt) + self.dt * ( self.memoize('ev100In',t-self.dt) + self.memoize('ev200In',t-self.dt) + self.memoize('ev300In',t-self.dt) - ( self.memoize('bevOutA',t-self.dt) + self.memoize('bevOutB',t-self.dt) + self.memoize('bevOutC',t-self.dt) + self.memoize('bevOutD',t-self.dt) ) )) ),
        'hybStock'          : lambda t: ( (max([0 , 3.57392])) if ( t  <=  self.starttime ) else (self.memoize('hybStock',t-self.dt) + self.dt * ( self.memoize('hybIn',t-self.dt) - ( self.memoize('hybOutA',t-self.dt) + self.memoize('hybOutB',t-self.dt) + self.memoize('hybOutC',t-self.dt) + self.memoize('hybOutD',t-self.dt) ) )) ),
        'phev10Stock'          : lambda t: ( (max([0 , 3.57392])) if ( t  <=  self.starttime ) else (self.memoize('phev10Stock',t-self.dt) + self.dt * ( self.memoize('phev10In',t-self.dt) - ( self.memoize('phev10OutA',t-self.dt) + self.memoize('phev10OutB',t-self.dt) + self.memoize('phev10OutC',t-self.dt) + self.memoize('phev10OutD',t-self.dt) ) )) ),
        'phev40Stock'          : lambda t: ( (max([0 , 3.57392])) if ( t  <=  self.starttime ) else (self.memoize('phev40Stock',t-self.dt) + self.dt * ( self.memoize('phev40In',t-self.dt) - ( self.memoize('phev40OutA',t-self.dt) + self.memoize('phev40OutB',t-self.dt) + self.memoize('phev40OutC',t-self.dt) + self.memoize('phev40OutD',t-self.dt) ) )) ),
        'remanCapacity'          : lambda t: ( (500000.0) if ( t  <=  self.starttime ) else (self.memoize('remanCapacity',t-self.dt) + self.dt * ( self.memoize('capacityAddition',t-self.dt) )) ),
        'slbStock'          : lambda t: ( (max([0 , 3.57392])) if ( t  <=  self.starttime ) else (self.memoize('slbStock',t-self.dt) + self.dt * ( self.memoize('slbIn',t-self.dt) - ( self.memoize('slbOutA',t-self.dt) + self.memoize('slbOutB',t-self.dt) + self.memoize('slbOutC',t-self.dt) + self.memoize('slbOutD',t-self.dt) ) )) ),
        
    
        # Flows
        'bevOutA'             : lambda t: max([0 , 0.1 * self.memoize('bevStock', t) / 6.0]),
        'bevOutB'             : lambda t: max([0 , 0.4 * self.memoize('bevStock', t) / 8.0]),
        'bevOutC'             : lambda t: max([0 , 0.4 * self.memoize('bevStock', t) / 10.0]),
        'bevOutD'             : lambda t: max([0 , 0.1 * self.memoize('bevStock', t) / 12.0]),
        'capacityAddition'             : lambda t: max([0 , ( (self.memoize('additionOverNYears', t)) if ( t  > self.memoize('startYearForReman', t)) else (0.0) )]),
        'ev100In'             : lambda t: max([0 ,  t ]),
        'ev200In'             : lambda t: max([0 ,  t ]),
        'ev300In'             : lambda t: max([0 ,  t ]),
        'hybIn'             : lambda t: max([0 ,  t ]),
        'hybOutA'             : lambda t: max([0 , 0.1 * self.memoize('hybStock', t) / 6.0]),
        'hybOutB'             : lambda t: max([0 , 0.4 * self.memoize('hybStock', t) / 8.0]),
        'hybOutC'             : lambda t: max([0 , 0.4 * self.memoize('hybStock', t) / 10.0]),
        'hybOutD'             : lambda t: max([0 , 0.1 * self.memoize('hybStock', t) / 12.0]),
        'phev10In'             : lambda t: max([0 ,  t ]),
        'phev10OutA'             : lambda t: max([0 , 0.1 * self.memoize('phev10Stock', t) / 6.0]),
        'phev10OutB'             : lambda t: max([0 , 0.4 * self.memoize('phev10Stock', t) / 8.0]),
        'phev10OutC'             : lambda t: max([0 , 0.4 * self.memoize('phev10Stock', t) / 10.0]),
        'phev10OutD'             : lambda t: max([0 , 0.1 * self.memoize('phev10Stock', t) / 12.0]),
        'phev40In'             : lambda t: max([0 ,  t ]),
        'phev40OutA'             : lambda t: max([0 , 0.1 * self.memoize('phev40Stock', t) / 6.0]),
        'phev40OutB'             : lambda t: max([0 , 0.4 * self.memoize('phev40Stock', t) / 8.0]),
        'phev40OutC'             : lambda t: max([0 , 0.4 * self.memoize('phev40Stock', t) / 10.0]),
        'phev40OutD'             : lambda t: max([0 , 0.1 * self.memoize('phev40Stock', t) / 12.0]),
        'slbIn'             : lambda t: max([0 , self.memoize('remanSlb', t)]),
        'slbOutA'             : lambda t: max([0 , 0.1 * self.memoize('slbStock', t) / 3.0]),
        'slbOutB'             : lambda t: max([0 , 0.4 * self.memoize('slbStock', t) / 4.0]),
        'slbOutC'             : lambda t: max([0 , 0.4 * self.memoize('slbStock', t) / 5.0]),
        'slbOutD'             : lambda t: max([0 , 0.1 * self.memoize('slbStock', t) / 6.0]),
        
    
        # converters
        'additionOverNYears'      : lambda t: ( (( self.memoize('remanSlbPossible', t) - self.memoize('remanCapacity', t) )) if (self.memoize('remanSlbPossible', t) > self.memoize('remanCapacity', t)) else (0.0) ),
        'allowableMaxCost'      : lambda t: self.memoize('sellingPriceOfSlb', t) / ( 1.0 + self.memoize('allowableProfit%', t) ),
        'allowableMaxCostWithoutOverheads'      : lambda t: self.memoize('allowableMaxCost', t) - self.memoize('overheadAndLaunchCosts', t),
        'allowableProfit%'      : lambda t: 0.1,
        'aluminumAfterRecycl'      : lambda t: self.memoize('aluminumRe', t) * self.memoize('aluminumFraction', t) * self.memoize('recycledeolb', t),
        'aluminumDemandModified'      : lambda t: self.memoize('aluminumIn', t) - self.memoize('aluminumAfterRecycl', t),
        'aluminumFraction'      : lambda t: ( self.memoize('licoo2Fraction', t) * 0.304 ) + ( self.memoize('limn2o4Fraction', t) * 0.075 ) + ( self.memoize('lifepo4Fraction', t) * 0.457 ) + ( self.memoize('nmcFraction', t) * 0.263 ),
        'aluminumIn'      : lambda t: self.memoize('aluminumFraction', t) * self.memoize('totalLibDemand', t),
        'aluminumRe'      : lambda t: 0.42,
        'bevBatteryEnergy'      : lambda t: 39.0,
        'bevBatteryEnergyInPerYear'      : lambda t: self.memoize('bevBatteryEnergy', t) * ( self.memoize('ev100In', t) + self.memoize('ev200In', t) + self.memoize('ev300In', t) ),
        'bevBatteryEnergyOutPerYear'      : lambda t: self.memoize('bevBatteryEnergy', t) * self.memoize('totalBevOut', t),
        'cobaltAfterRecycl'      : lambda t: self.memoize('cobaltRe', t) * self.memoize('cobaltFraction', t) * self.memoize('recycledeolb', t),
        'cobaltDemandModified'      : lambda t: self.memoize('cobaltIn', t) - self.memoize('cobaltAfterRecycl', t),
        'cobaltFraction'      : lambda t: ( self.memoize('licoo2Fraction', t) * 1.01 ) + ( self.memoize('limn2o4Fraction', t) * 0.0 ) + ( self.memoize('lifepo4Fraction', t) * 0.0 ) + ( self.memoize('nmcFraction', t) * 0.483 ),
        'cobaltIn'      : lambda t: self.memoize('cobaltFraction', t) * self.memoize('totalLibDemand', t),
        'cobaltRe'      : lambda t: 0.89,
        'collectedeolb'      : lambda t: self.memoize('collectionefficiency', t) * self.memoize('sumTotalCapEolBat', t),
        'collectionefficiency'      : lambda t: 1.0,
        'copperAfterRecycl'      : lambda t: self.memoize('copperRe', t) * self.memoize('copperFraction', t) * self.memoize('recycledeolb', t),
        'copperDemandModified'      : lambda t: self.memoize('copperIn', t) - self.memoize('copperAfterRecycl', t),
        'copperFraction'      : lambda t: ( self.memoize('licoo2Fraction', t) * 0.426 ) + ( self.memoize('limn2o4Fraction', t) * 0.075 ) + ( self.memoize('lifepo4Fraction', t) * 0.571 ) + ( self.memoize('nmcFraction', t) * 0.39 ),
        'copperIn'      : lambda t: self.memoize('copperFraction', t) * self.memoize('totalLibDemand', t),
        'copperRe'      : lambda t: 0.9,
        'costOfElectricity'      : lambda t: ( (0.0) if ( t  < self.memoize('startYearForReman', t)) else (( ( (( ( (self.memoize('maxCostOfElectricity', t)) if (self.memoize('costOfElectricityPerKwh', t) > self.memoize('maxCostOfElectricity', t)) else (self.memoize('costOfElectricityPerKwh', t)) ) )) if (self.memoize('costOfElectricityPerKwh', t) > self.memoize('minCostOfElectricity', t)) else (self.memoize('minCostOfElectricity', t)) ) )) ),
        'costOfElectricityPerKwh'      : lambda t: self.memoize('costOfElectricityPerSlbKwh', t) / ( self.memoize('electricityPerKwh', t) * ( 1.0 + self.memoize('technicallyFeasibleBatteriesFraction', t) ) ),
        'costOfElectricityPerSlbKwh'      : lambda t: self.memoize('allowableMaxCostWithoutOverheads', t) - self.memoize('totalCostPerSlbKwhNoElectricity', t),
        'costOfLaborInFacility'      : lambda t: self.memoize('costOfLaborPerHour', t) * self.memoize('numberOfHoursPerYearPerLaborer', t) * self.memoize('minLaborNeeded', t),
        'costOfLaborPerHour'      : lambda t: 20.67,
        'costOfLaborPerSlbKwh'      : lambda t: self.memoize('costOfLaborPerSlbKwhWithoutIncrease', t) + self.memoize('increaseInLaborCost', t),
        'costOfLaborPerSlbKwhWithoutIncrease'      : lambda t: self.memoize('costOfLaborInFacility', t) / self.memoize('remanSlb', t),
        'costOfMaterialsConstantBasedOnMassPerKwh'      : lambda t: ( 7.0 / self.memoize('kwh/kg', t) ) / 23.0,
        'costOfMaterialsConstantPerKwh'      : lambda t: ( 15.0 + 20.0 + 30.0 ) / 23.0,
        'costOfMaterialsOthersPerKwh'      : lambda t: ( 30.0 + 10.0 ) / 23.0,
        'costOfMaterialsPerSlbKwh'      : lambda t: self.memoize('costOfMaterialsConstantPerKwh', t) + self.memoize('costOfMaterialsOthersPerKwh', t) + self.memoize('costOfMaterialsConstantBasedOnMassPerKwh', t),
        'costOfRemanCapacity'      : lambda t: ( ( 1124990.0 / 10.0 ) + 1192854.0 ) / 115000.0,
        'costOfRemanCapacityPerSlbKwh'      : lambda t: self.memoize('costOfRemanCapacityTotal', t) / self.memoize('remanSlb', t),
        'costOfRemanCapacityTotal'      : lambda t: self.memoize('remanCapacity', t) * self.memoize('costOfRemanCapacity', t),
        'electricityPerKwh'      : lambda t: 7.5,
        'eolRecyclingValue'      : lambda t: self.memoize('recycledeolb', t) * self.memoize('recycledMaterialValue', t) / 1000000.0,
        'hybBatteryEnergy'      : lambda t: 5.3,
        'hybBatteryEnergyInPerYear'      : lambda t: self.memoize('hybBatteryEnergy', t) * self.memoize('hybIn', t),
        'hybBatteryEnergyOutPerYear'      : lambda t: self.memoize('hybBatteryEnergy', t) * self.memoize('totalHybOut', t),
        'increaseInLaborCost'      : lambda t: self.memoize('costOfLaborPerSlbKwhWithoutIncrease', t) * (  t  - 2019.0 ) * self.memoize('percentageIncreaseInLaborCost', t),
        'ironAfterRecycl'      : lambda t: self.memoize('ironRe', t) * self.memoize('ironFraction', t) * self.memoize('recycledeolb', t),
        'ironDemandModified'      : lambda t: self.memoize('ironIn', t) - self.memoize('ironAfterRecycl', t),
        'ironFraction'      : lambda t: ( self.memoize('licoo2Fraction', t) * 0.0 ) + ( self.memoize('limn2o4Fraction', t) * 0.0 ) + ( self.memoize('lifepo4Fraction', t) * 0.68 ) + ( self.memoize('nmcFraction', t) * 0.0 ),
        'ironIn'      : lambda t: self.memoize('ironFraction', t) * self.memoize('totalLibDemand', t),
        'ironRe'      : lambda t: 0.52,
        'kwh/kg'      : lambda t: 0.15,
        'laborInFacility'      : lambda t: 10.0,
        'licoo2Fraction'      : lambda t: 0.1,
        'lifepo4Fraction'      : lambda t: 0.3,
        'limn2o4Fraction'      : lambda t: 0.3,
        'lithiumAfterRecycl'      : lambda t: self.memoize('lithiumRe', t) * self.memoize('lithiumFraction', t) * self.memoize('recycledeolb', t),
        'lithiumDemandModified'      : lambda t: self.memoize('lithiumIn', t) - self.memoize('lithiumAfterRecycl', t),
        'lithiumFraction'      : lambda t: ( self.memoize('licoo2Fraction', t) * 0.119 ) + ( self.memoize('limn2o4Fraction', t) * 0.104 ) + ( self.memoize('lifepo4Fraction', t) * 0.084 ) + ( self.memoize('nmcFraction', t) * 0.057 ),
        'lithiumIn'      : lambda t: self.memoize('lithiumFraction', t) * self.memoize('totalLibDemand', t),
        'lithiumRe'      : lambda t: 0.0,
        'manganeseAfterRecycl'      : lambda t: self.memoize('manganeseRe', t) * self.memoize('manganeseFraction', t) * self.memoize('recycledeolb', t),
        'manganeseDemandModified'      : lambda t: self.memoize('manganeseIn', t) - self.memoize('manganeseAfterRecycl', t),
        'manganeseFraction'      : lambda t: ( self.memoize('licoo2Fraction', t) * 0.0 ) + ( self.memoize('limn2o4Fraction', t) * 1.37 ) + ( self.memoize('lifepo4Fraction', t) * 0.0 ) + ( self.memoize('nmcFraction', t) * 0.451 ),
        'manganeseIn'      : lambda t: self.memoize('manganeseFraction', t) * self.memoize('totalLibDemand', t),
        'manganeseRe'      : lambda t: 0.0,
        'maxCostOfElectricity'      : lambda t: 0.0688 * 1.5,
        'minCostOfElectricity'      : lambda t: 0.0688 / 2.0,
        'minLaborNeeded'      : lambda t: min([self.memoize('numberOfLaborersNeeded', t) , ( self.memoize('laborInFacility', t) * self.memoize('remanCapacity', t) / 115000.0 )]),
        'modifiedLibDemand'      : lambda t: ( (self.memoize('totalLibDemand', t) - self.memoize('remanSlb', t)) if ( t  > self.memoize('startYearForReman', t)) else (self.memoize('totalLibDemand', t)) ),
        'nickelAfterRecycl'      : lambda t: self.memoize('nickelRe', t) * self.memoize('nickelFraction', t) * self.memoize('recycledeolb', t),
        'nickelDemandModified'      : lambda t: self.memoize('nickelIn', t) - self.memoize('nickelAfterRecycl', t),
        'nickelFraction'      : lambda t: ( self.memoize('licoo2Fraction', t) * 0.071 ) + ( self.memoize('limn2o4Fraction', t) * 0.0 ) + ( self.memoize('lifepo4Fraction', t) * 0.0 ) + ( self.memoize('nmcFraction', t) * 0.482 ),
        'nickelIn'      : lambda t: self.memoize('nickelFraction', t) * self.memoize('totalLibDemand', t),
        'nickelRe'      : lambda t: 0.62,
        'nmcFraction'      : lambda t: 0.3,
        'numberOfHoursPerYearPerLaborer'      : lambda t: 8.0 * 252.0,
        'numberOfLaborersNeeded'      : lambda t: self.memoize('remanSlb', t) / ( self.memoize('outputPerHourKwh', t) * self.memoize('numberOfHoursPerYearPerLaborer', t) * self.memoize('numberOfShifts', t) ),
        'numberOfShifts'      : lambda t: 3.0,
        'outputPerHour'      : lambda t: 3.0,
        'outputPerHourKwh'      : lambda t: 10.0 * self.memoize('outputPerHour', t),
        'overheadAndLaunchCosts'      : lambda t: ( 0.05 * self.memoize('costOfMaterialsPerSlbKwh', t) ) + ( 0.65 * self.memoize('costOfLaborPerSlbKwh', t) ),
        'percentageIncreaseInLaborCost'      : lambda t: 0.028,
        'percentageIncreaseInTransportationCost'      : lambda t: 0.03,
        'phev10BatteryEnergy'      : lambda t: 4.4,
        'phev10BatteryEnergyInPerYear'      : lambda t: self.memoize('phev10BatteryEnergy', t) * self.memoize('phev10In', t),
        'phev10BatteryEnergyOutPerYear'      : lambda t: self.memoize('phev10BatteryEnergy', t) * self.memoize('totalPhev10Out', t),
        'phev40BatteryEnergy'      : lambda t: 18.0,
        'phev40BatteryEnergyInPerYear'      : lambda t: self.memoize('phev40BatteryEnergy', t) * self.memoize('phev40In', t),
        'phev40BatteryEnergyOutPerYear'      : lambda t: self.memoize('phev40BatteryEnergy', t) * self.memoize('totalPhev40Out', t),
        'ppEa'      : lambda t: 0.37,
        'ppGp'      : lambda t: 0.44,
        'ppTotal'      : lambda t: ( (self.memoize('ppGp', t)) if ( t  > ( self.memoize('yearOfSwitchFromEaToGp', t) - 1.0 )) else (self.memoize('ppEa', t)) ),
        'recycledMaterialValue'      : lambda t: self.memoize('recycledMaterialValueIn2020', t) + ( (abs(self.memoize('recycledMaterialValueIn2020', t))) * self.memoize('recycledMaterialValuePercentIncrease', t) * (  t  - 2020.0 ) ),
        'recycledMaterialValueIn2020'      : lambda t: -4.1,
        'recycledMaterialValuePercentIncrease'      : lambda t: 0.1,
        'recycledeolb'      : lambda t: ( (self.memoize('collectedeolb', t) - self.memoize('remanSlb', t) + self.memoize('totalSlbOut', t)) if ( t  > self.memoize('startYearForReman', t)) else (0.0) ),
        'remanSlb'      : lambda t: self.memoize('remanCapacity', t) / self.memoize('technicallyFeasibleBatteriesFraction', t),
        'remanSlbPossible'      : lambda t: ( (self.memoize('slbdemand', t)) if (self.memoize('technicallyFeasibleCollectedeolb', t) > self.memoize('slbdemand', t)) else (self.memoize('technicallyFeasibleCollectedeolb', t)) ),
        'sellingPriceOfSlb'      : lambda t: self.memoize('valueParameter', t) * self.memoize('usedProductDiscountFactor', t) * self.memoize('costOfNewBatteryBnef', t),
        'slbTonnes'      : lambda t: 1.1 / ( self.memoize('kwh/kg', t) * 1000.0 ),
        'slbdemand'      : lambda t: ( (self.memoize('demandForEnergyStorage', t) * self.memoize('ppTotal', t)) if ( t  > ( self.memoize('startYearForReman', t) - 1.0 )) else (0.0) ),
        'startYearForReman'      : lambda t: 2020.0,
        'startYearForReman1'      : lambda t: 2020.0,
        'steelAfterRecycl'      : lambda t: self.memoize('steelRe', t) * self.memoize('steelFraction', t) * self.memoize('recycledeolb', t),
        'steelDemandModified'      : lambda t: self.memoize('steelIn', t) - self.memoize('steelAfterRecycl', t),
        'steelFraction'      : lambda t: ( self.memoize('licoo2Fraction', t) * 0.963 ) + ( self.memoize('limn2o4Fraction', t) * 1.105 ) + ( self.memoize('lifepo4Fraction', t) * 2.348 ) + ( self.memoize('nmcFraction', t) * 0.866 ),
        'steelIn'      : lambda t: self.memoize('steelFraction', t) * self.memoize('totalLibDemand', t),
        'steelRe'      : lambda t: 0.52,
        'sumTotalCapEolBat'      : lambda t: self.memoize('totalEvBatteryEnergyPerYear', t) * self.memoize('valueOfThroughputOldBattery', t),
        'sumTotalCapInBat'      : lambda t: self.memoize('phev40BatteryEnergyInPerYear', t) + self.memoize('hybBatteryEnergyInPerYear', t) + self.memoize('phev10BatteryEnergyInPerYear', t) + self.memoize('bevBatteryEnergyInPerYear', t),
        'technicallyFeasibleBatteriesFraction'      : lambda t: 0.95,
        'technicallyFeasibleCollectedeolb'      : lambda t: self.memoize('collectedeolb', t) * self.memoize('technicallyFeasibleBatteriesFraction', t),
        'tonnePerSlbKwh'      : lambda t: 0.00110231 / self.memoize('kwh/kg', t),
        'totalBevOut'      : lambda t: self.memoize('bevOutA', t) + self.memoize('bevOutB', t) + self.memoize('bevOutC', t) + self.memoize('bevOutD', t),
        'totalCostPerSlbKwhNoElectricity'      : lambda t: self.memoize('transportationCostsPerSlbKwh', t) + self.memoize('costOfRemanCapacityPerSlbKwh', t) + self.memoize('costOfLaborPerSlbKwh', t) + self.memoize('costOfMaterialsPerSlbKwh', t),
        'totalEvBatteryEnergyPerYear'      : lambda t: self.memoize('bevBatteryEnergyOutPerYear', t) + self.memoize('hybBatteryEnergyOutPerYear', t) + self.memoize('phev10BatteryEnergyOutPerYear', t) + self.memoize('phev40BatteryEnergyOutPerYear', t),
        'totalHybOut'      : lambda t: self.memoize('hybOutA', t) + self.memoize('hybOutB', t) + self.memoize('hybOutC', t) + self.memoize('hybOutD', t),
        'totalLibDemand'      : lambda t: self.memoize('demandForEnergyStorage', t) + self.memoize('sumTotalCapInBat', t),
        'totalPhev10Out'      : lambda t: self.memoize('phev10OutA', t) + self.memoize('phev10OutB', t) + self.memoize('phev10OutC', t) + self.memoize('phev10OutD', t),
        'totalPhev40Out'      : lambda t: self.memoize('phev40OutA', t) + self.memoize('phev40OutB', t) + self.memoize('phev40OutC', t) + self.memoize('phev40OutD', t),
        'totalSlbOut'      : lambda t: self.memoize('slbOutA', t) + self.memoize('slbOutB', t) + self.memoize('slbOutC', t) + self.memoize('slbOutD', t),
        'transporationCostPerMile'      : lambda t: 2.16,
        'transportCostPerKwh'      : lambda t: self.memoize('transportationCostsPerTonmile', t) * self.memoize('transportDistancePossible', t) * self.memoize('tonnePerSlbKwh', t),
        'transportDistanceFromRemanCapacity'      : lambda t: 2524.2424 - ( self.memoize('remanCapacity', t) / 20625.0 ),
        'transportDistanceMinInput'      : lambda t: 100.0,
        'transportDistancePossible'      : lambda t: max([self.memoize('transportDistanceMinInput', t) , self.memoize('transportDistanceFromRemanCapacity', t)]),
        'transportTruckTonnage'      : lambda t: 16.0,
        'transportationCostsPerMileForTheYear'      : lambda t: self.memoize('transporationCostPerMile', t) * (  t  - 2019.0 ) * self.memoize('percentageIncreaseInTransportationCost', t),
        'transportationCostsPerSlbKwh'      : lambda t: self.memoize('transportCostPerKwh', t) / ( 1.0 + self.memoize('technicallyFeasibleBatteriesFraction', t) ),
        'transportationCostsPerTonmile'      : lambda t: self.memoize('transportationCostsPerMileForTheYear', t) / self.memoize('transportTruckTonnage', t),
        'updf'      : lambda t: ( (self.memoize('updfGp', t)) if ( t  > ( self.memoize('yearOfSwitchFromEaToGp1', t) - 1.0 )) else (self.memoize('updfEa', t)) ),
        'updfEa'      : lambda t: 0.6152,
        'updfGp'      : lambda t: 0.5853,
        'usedProductDiscountFactor'      : lambda t: ( (0.0) if ( t  < self.memoize('startYearForReman1', t)) else (self.memoize('updf', t)) ),
        'valueOfThroughputNewBattery'      : lambda t: 1.0,
        'valueOfThroughputOldBattery'      : lambda t: 0.8,
        'valueParameter'      : lambda t: self.memoize('valueOfThroughputOldBattery', t) / self.memoize('valueOfThroughputNewBattery', t),
        'yearOfSwitchFromEaToGp'      : lambda t: 2028.0,
        'yearOfSwitchFromEaToGp1'      : lambda t: 2028.0,
        
    
        # gf
        'costOfNewBatteryBnef' : lambda t: LERP(  t , self.points['costOfNewBatteryBnef']),
        'demandForEnergyStorage' : lambda t: LERP(  t , self.points['demandForEnergyStorage']),
        
    
        #constants
        
    
    
        }
    
        self.points = {
            'costOfNewBatteryBnef' :  [(2010.0, 1160.0), (2011.0, 899.0), (2012.0, 707.0), (2013.0, 650.0), (2014.0, 577.0), (2015.0, 373.0), (2016.0, 288.0), (2017.0, 214.0), (2018.0, 176.0), (2019.0, 162.3333333), (2020.0, 148.6666667), (2021.0, 135.0), (2022.0, 121.3333333), (2023.0, 107.6666667), (2024.0, 94.0), (2025.0, 88.66666667), (2026.0, 83.33333333), (2027.0, 78.0), (2028.0, 72.66666667), (2029.0, 67.33333333), (2030.0, 62.0), (2031.0, 61.38), (2032.0, 60.7662), (2033.0, 60.158538), (2034.0, 59.55695262), (2035.0, 58.96138309), (2036.0, 58.37176926), (2037.0, 57.78805157), (2038.0, 57.21017105), (2039.0, 56.63806934), (2040.0, 56.07168865), (2041.0, 55.51097176), (2042.0, 54.95586205), (2043.0, 54.40630343), (2044.0, 53.86224039), (2045.0, 53.32361799), (2046.0, 52.79038181), (2047.0, 52.26247799), (2048.0, 51.73985321), (2049.0, 51.22245468), (2050.0, 50.71023013)]  , 'demandForEnergyStorage' :  [(2020.0, 2666670.0), (2022.0, 4000000.0), (2024.0, 5333330.0), (2026.0, 5333330.0), (2028.0, 4000000.0), (2030.0, 2666670.0), (2032.0, 2666670.0), (2034.0, 4000000.0), (2036.0, 6666670.0), (2038.0, 9333330.0), (2040.0, 18666670.0), (2042.0, 25333330.0), (2044.0, 33333330.0), (2046.0, 50666670.0), (2048.0, 104000000.0), (2050.0, 165333330.0)]  , 
        }
    
    
        self.dimensions = {
        	'': {
                'labels': [  ],
                'variables': [  ],
            },
        }
                
        self.dimensions_order = {}     
    
        self.stocks = ['bevStock',   'hybStock',   'phev10Stock',   'phev40Stock',   'remanCapacity',   'slbStock'  ]
        self.flows = ['bevOutA',   'bevOutB',   'bevOutC',   'bevOutD',   'capacityAddition',   'ev100In',   'ev200In',   'ev300In',   'hybIn',   'hybOutA',   'hybOutB',   'hybOutC',   'hybOutD',   'phev10In',   'phev10OutA',   'phev10OutB',   'phev10OutC',   'phev10OutD',   'phev40In',   'phev40OutA',   'phev40OutB',   'phev40OutC',   'phev40OutD',   'slbIn',   'slbOutA',   'slbOutB',   'slbOutC',   'slbOutD'  ]
        self.converters = ['additionOverNYears',   'allowableMaxCost',   'allowableMaxCostWithoutOverheads',   'allowableProfit%',   'aluminumAfterRecycl',   'aluminumDemandModified',   'aluminumFraction',   'aluminumIn',   'aluminumRe',   'bevBatteryEnergy',   'bevBatteryEnergyInPerYear',   'bevBatteryEnergyOutPerYear',   'cobaltAfterRecycl',   'cobaltDemandModified',   'cobaltFraction',   'cobaltIn',   'cobaltRe',   'collectedeolb',   'collectionefficiency',   'copperAfterRecycl',   'copperDemandModified',   'copperFraction',   'copperIn',   'copperRe',   'costOfElectricity',   'costOfElectricityPerKwh',   'costOfElectricityPerSlbKwh',   'costOfLaborInFacility',   'costOfLaborPerHour',   'costOfLaborPerSlbKwh',   'costOfLaborPerSlbKwhWithoutIncrease',   'costOfMaterialsConstantBasedOnMassPerKwh',   'costOfMaterialsConstantPerKwh',   'costOfMaterialsOthersPerKwh',   'costOfMaterialsPerSlbKwh',   'costOfRemanCapacity',   'costOfRemanCapacityPerSlbKwh',   'costOfRemanCapacityTotal',   'electricityPerKwh',   'eolRecyclingValue',   'hybBatteryEnergy',   'hybBatteryEnergyInPerYear',   'hybBatteryEnergyOutPerYear',   'increaseInLaborCost',   'ironAfterRecycl',   'ironDemandModified',   'ironFraction',   'ironIn',   'ironRe',   'kwh/kg',   'laborInFacility',   'licoo2Fraction',   'lifepo4Fraction',   'limn2o4Fraction',   'lithiumAfterRecycl',   'lithiumDemandModified',   'lithiumFraction',   'lithiumIn',   'lithiumRe',   'manganeseAfterRecycl',   'manganeseDemandModified',   'manganeseFraction',   'manganeseIn',   'manganeseRe',   'maxCostOfElectricity',   'minCostOfElectricity',   'minLaborNeeded',   'modifiedLibDemand',   'nickelAfterRecycl',   'nickelDemandModified',   'nickelFraction',   'nickelIn',   'nickelRe',   'nmcFraction',   'numberOfHoursPerYearPerLaborer',   'numberOfLaborersNeeded',   'numberOfShifts',   'outputPerHour',   'outputPerHourKwh',   'overheadAndLaunchCosts',   'percentageIncreaseInLaborCost',   'percentageIncreaseInTransportationCost',   'phev10BatteryEnergy',   'phev10BatteryEnergyInPerYear',   'phev10BatteryEnergyOutPerYear',   'phev40BatteryEnergy',   'phev40BatteryEnergyInPerYear',   'phev40BatteryEnergyOutPerYear',   'ppEa',   'ppGp',   'ppTotal',   'recycledMaterialValue',   'recycledMaterialValueIn2020',   'recycledMaterialValuePercentIncrease',   'recycledeolb',   'remanSlb',   'remanSlbPossible',   'sellingPriceOfSlb',   'slbTonnes',   'slbdemand',   'startYearForReman',   'startYearForReman1',   'steelAfterRecycl',   'steelDemandModified',   'steelFraction',   'steelIn',   'steelRe',   'sumTotalCapEolBat',   'sumTotalCapInBat',   'technicallyFeasibleBatteriesFraction',   'technicallyFeasibleCollectedeolb',   'tonnePerSlbKwh',   'totalBevOut',   'totalCostPerSlbKwhNoElectricity',   'totalEvBatteryEnergyPerYear',   'totalHybOut',   'totalLibDemand',   'totalPhev10Out',   'totalPhev40Out',   'totalSlbOut',   'transporationCostPerMile',   'transportCostPerKwh',   'transportDistanceFromRemanCapacity',   'transportDistanceMinInput',   'transportDistancePossible',   'transportTruckTonnage',   'transportationCostsPerMileForTheYear',   'transportationCostsPerSlbKwh',   'transportationCostsPerTonmile',   'updf',   'updfEa',   'updfGp',   'usedProductDiscountFactor',   'valueOfThroughputNewBattery',   'valueOfThroughputOldBattery',   'valueParameter',   'yearOfSwitchFromEaToGp',   'yearOfSwitchFromEaToGp1'  ]
        self.gf = ['costOfNewBatteryBnef',   'demandForEnergyStorage'  ]
        self.constants= []
        self.events = [
            ]
    
        self.memo = {}
        for key in list(self.equations.keys()):
          self.memo[key] = {}  # DICT OF DICTS!
          
    
    """
    Builtin helpers
    """
    def ramp(self,slope,start,t):
        if not start:
            start = self.starttime
        if t <= start: return 0
        return (t-start)*slope
        
    def rootn(self,expression,order):
        order = round(order,0)
        if expression < 0 and order % 2 == 0: # Stella does not allow even roots for negative numbers as no complex numbers are supported
            return np.nan
        return -abs(expression)**(1/round(order,0)) if expression < 0 else abs(expression)**(1/round(order,0)) # Stella Logic! No Complex numbers for negative numbers. Hence take the nth root of the absolute value and then add the negativity (if any)
    
    """
    Statistical builtins with Seed
    """
    def pareto_with_seed(self, shape, scale, seed, t):
        if t == self.starttime:
            np.random.seed(int(seed))
        return np.random.pareto(shape) * scale  
    
    def weibull_with_seed(self, shape, scale, seed, t):
        if t == self.starttime:
            np.random.seed(int(seed))
        return np.random.weibull(shape) * scale      
    
    def poisson_with_seed(self, mu, seed, t):
        if t == self.starttime:
            np.random.seed(int(seed))
        return np.random.poisson(mu)   
    
    def negbinomial_with_seed(self, successes, p, seed, t):
        if t == self.starttime:
            np.random.seed(int(seed))
        return np.random.negative_binomial(successes, p)  
    
    def lognormal_with_seed(self, mean, stdev, seed, t):
        if t == self.starttime:
            np.random.seed(int(seed))
        return np.random.lognormal(mean, stdev)   
    
    def logistic_with_seed(self, mean, scale, seed, t):
        if t == self.starttime:
            np.random.seed(int(seed))
        return np.random.logistic(mean, scale)
    
    def random_with_seed(self, seed, t ):
        if t == self.starttime:
            random.seed(int(seed))
        return random.random()

    def beta_with_seed(self, a,b,seed, t):
        if t == self.starttime:
            np.random.seed(int(seed))
        return np.random.beta(a,b)
        
    def binomial_with_seed(self, n,p,seed, t):
        if t == self.starttime:
            np.random.seed(int(seed))
        return np.random.binomial(n,p)
        
    def gamma_with_seed(self, shape,scale,seed, t):
        if t == self.starttime:
            np.random.seed(int(seed))
        return np.random.gamma(shape,scale)
        
    def exprnd_with_seed(self, plambda,seed, t):
        if t == self.starttime:
            np.random.seed(int(seed))
        return np.random.exponential(plambda)
        
    def geometric_with_seed(self, p, seed, t):
        if t == self.starttime:
            np.random.seed(int(seed))
        return np.random.geometric(p)
    
    def triangular_with_seed(self, left, mode, right, seed, t):
        if t == self.starttime:
            np.random.seed(int(seed))
        return np.random.triangular(left, mode, right)
    
    def rank(self, lis, rank):
        rank = int(rank)
        sorted_list = sorted(lis)
        try:
            rankth_elem = sorted_list[rank-1]
        except IndexError as e:
            logging.error("RANK: Rank {} too high for array of size {}".format(rank,len(lis)))
        return lis.index(rankth_elem)+1
        

    def interpolate(self, variable, t, *args):
        """
        Helper for builtin "interpolate". Uses the arrayed variable and args to compute the interpolation
        :param variable:
        :param t:
        :param args: Interpolation weight for each dimension, between one or zero
        :return:
        """
        def compute_x(values): #
            """
            Compute x values for interpolation. Always from 0 to 1. E.g. values = [1,2,3], then x = [0, 0.5, 1.0]
            :param values:
            :return:
            """
            #
            x = [0]
            for i in range(1, len(values)): x += [x[i - 1] + 1 / (len(values) - 1)]
            return x

        def interpolate_values(index, y_val):  # Internal interpolate of a dimension's results
            x_val = compute_x(y_val)
            points = [(x_val[i], y_val[i]) for i in range(0, len(x_val))]
            return LERP(index, points)

        # Fix each weight to a value between 0 and 1
        args = [max(0,min(x,1)) for x in args]

        # Get dimensions of variable (2,3,4 ...)
        dimensions = self.dimensions_order[variable]

        # Get Labels
        labels = {key: dim["labels"] for key, dim in
                  dict(filter(lambda elem: elem[0] in dimensions, self.dimensions.items())).items()}

        # Compute
        results = {}
        if len(labels.keys()) == 1:
            return interpolate_values(args[0], self.equation(variable + "[*]", t))
        for index, dimension in enumerate(dimensions):
            results[dimension] = []
            for label in labels[dimension]:
                indices = ["*" if i != index else label for i in
                           range(0, len(dimensions))]  # Build indices, such as "*,element1" or "1,*"

                results[dimension] += [
                    interpolate_values(args[index], self.equation(variable + "[{}]".format(",".join(indices)), t))]

        return [interpolate_values(args[i], v) for i, v in enumerate(results.values())][0]

    def lookupinv(self,gf, value):
        """
        Helper for lookupinv builtin. Looks for the corresponding x of a given y
        :param gf: Name of graphical function
        :param value: Value we are looking for (y)
        :return:
        """
        def lerpfun(x, points):  # Special lerp function for the reversed points
            from scipy.interpolate import interp1d
            x_vals = np.array([x[0] for x in points])
            y_vals = np.array([x[1] for x in points])
            f = interp1d(x_vals, y_vals)
            return f(x)

        results = []
        for t in np.arange(self.starttime, self.stoptime + self.dt,
                           self.dt):  # Compute all y values for graphical functions using standard interpolate (LERP)
            results += [(LERP(t, self.points[gf]), t)] # y,x

        return np.round(lerpfun(value, results),
                     3)  # Use LERP function for the reversed set of points (y,x) and find the correct value. Cannot use standard LERP here because that would require continuous X (1,2,3..)

    def delay(self, tdelayed, offset, initial, t):
        '''
        Delay builtin
        :param tdelayed: Delayed T
        :param offset: Offset
        :param initial: Initial value
        :param t:
        :return:
        '''
        if (t - self.starttime) < offset: return initial
        else: return tdelayed

    def counter(self,start, interval, t):
        '''
        Counter bultin
        :param start:
        :param interval:
        :param t:
        :return:
        '''
        num_elems = (interval / start / self.dt)
        value = interval / num_elems
        t_copy = copy(t)

        while t >= interval: t = t - interval
        if (t_copy > interval): return (start + (t / self.dt) * value)

        return (t / self.dt * value)

    def npv(self, initial, p, t):
        """
        NPV (Net Present Value) builtin
        :param initial:
        :param p:
        :param t:
        :return:
        """
        rate = 1.0 / (1.0 + p) ** (t - self.dt - self.starttime + self.dt)
        return initial if (t <= self.starttime) else ( self.npv(initial, p, t - self.dt) + (self.dt * rate * initial) )# Recurse

    def irr(self, stock_name, missing, t,myname):
        """
        Approximate IRR (Internal Rate of Return)
        :param stock_name: Identifier of Stock to approximate for
        :param missing: Replace missing values with this value
        :param t:
        :return:
        """

        def compute_npv(stock_name, t, i, missing):
            I = missing if missing else self.equation(stock_name, self.starttime)
            return I + sum( [self.memoize(stock_name, t) / (1 + i) ** t for t in np.arange(self.starttime+self.dt , t, self.dt)])

        i = 0
        try:
            i = 0 if t <= self.starttime + self.dt else self.memo[myname][t-self.dt]
        except:
            pass

        if t == self.starttime: return None

        best_kw = {i : compute_npv(stock_name, t, i, missing)}
        for _ in range(0, 300):
            # Here we approximate the IRR
            kw = compute_npv(stock_name, t, i, missing)

            change = 0.001

            best_kw[i] = kw

            if abs(kw) < self.memoize(stock_name, t)*0.1: change = 0.0001

            if abs(kw) < self.memoize(stock_name, t)*0.05: change = 0.00001

            if abs(kw) < self.memoize(stock_name, t)*0.02: change = 0.000001

            if kw < 0: i -= change
            elif kw > 0:  i += change

            if kw == 0: return i
        best_kw = {k: v for k, v in sorted(best_kw.items(), key=lambda item: item[1])}
        x = {v: k for k, v in sorted(best_kw.items(), key=lambda item: item[1])} # Sort by best npv
        return x[min(x.keys())]

    def normalcdf(self,left, right, mean, sigma):
        import scipy.stats
        right = scipy.stats.norm(float(mean), float(sigma)).cdf(float(right))
        left = scipy.stats.norm(float(mean), float(sigma)).cdf(float(left))
        return round(right - left, 3)

    def cgrowth(self, p):
        from sympy.core.numbers import Float
        import sympy as sy
        z = sy.symbols('z', real=True) # We want to find z
        dt = self.dt

        x = (1 + dt * (1 * z))

        for i in range(1, int(1 / dt)): x = (x + dt * (x * z))

        # Definition of the equation to be solved
        eq = sy.Eq(1 + p, x)

        # Solve the equation
        results = [x for x in (sy.solve(eq)) if type(x) is Float and x > 0] # Quadratic problem, hence usually a positive, negative and 2 complex solutions. We only require the positive one
        return float(results[0])

    def montecarlo(self,probability,seed, t):
        """
        Montecarlo builtin
        :param probability:
        :param seed:
        :param t:
        :return:
        """
        if seed and t==self.starttime:
            random.seed(seed)
        rndnumber = random.uniform(0,100)
        return 1 if rndnumber < (probability*self.dt) else 0


    def derivn(self, equation, order, t):
        """
        nth derivative of an equation
        :param equation: Name of the equation
        :param order: n
        :param t: current t
        :return:
        """
        memo = {}
        dt = 0.25

        def mem(eq, t):
            """
            Memo for internal equations
            :param eq:
            :param t:
            :return:
            """
            if not eq in memo.keys(): memo[eq] = {}
            mymemo = memo[eq]
            if t in mymemo.keys(): return mymemo[t]
            else:
                mymemo[t] = s[eq](t)
                return mymemo[t]

        s = {}
        s[1] = lambda t: 0 if t <= self.starttime else (self.memoize(equation, t) - self.memoize(equation, t - dt)) / dt

        def addEquation(n):
            s[n] = lambda t: 0 if t <= self.starttime else (mem(n - 1, t) - mem(n - 1, t - dt)) / dt

        for n in list(range(2, order + 1)): addEquation(n)

        return s[order](t) if ( t >= self.starttime + (dt * order) ) else 0

    def smthn(self, inputstream, averaging_time, initial, n, t):
        """
        Pretty complex operator. Actually we are building a whole model here and have it run
        Find info in https://www.iseesystems.com/resources/help/v1-9/default.htm#08-Reference/07-Builtins/Delay_builtins.htm#kanchor364
        :param inputstream:
        :param averaging_time:
        :param initial:
        :param n:
        :param t:
        :return:
        """
        memo = {}
        dt = self.dt
        from copy import deepcopy

        def mem(eq, t):
            """
            Internal memo for equations
            :param eq:
            :param t:
            :return:
            """
            if not eq in memo.keys(): memo[eq] = {}
            mymemo = memo[eq]
            if t in mymemo.keys():return mymemo[t]
            else:
                mymemo[t] = s[eq](t)
                return mymemo[t]

        s = {}

        def addEquation(n, upper):
            y = deepcopy(n)
            if y == 1:
                s["stock1"] = lambda t: (
                    (max([0, (self.memoize(inputstream, t) if (initial is None) else initial)])) if (
                                t <= self.starttime) else (
                                mem('stock1', t - dt) + dt * (mem('changeInStock1', t - dt))))
                s['changeInStock1'] = lambda t: (self.memoize(inputstream, t) - mem('stock1', t)) / (
                            averaging_time / upper)
            if y > 1:
                s["stock{}".format(y)] = lambda t: (
                    (max([0, (self.memoize(inputstream, t) if (initial is None) else initial)])) if (t <= self.starttime) else (
                                mem("stock{}".format(y), t - dt) + dt * (mem('changeInStock{}'.format(y), t - dt))))
                s['changeInStock{}'.format(y)] = lambda t: (mem("stock{}".format(y - 1), t) - mem("stock{}".format(y),
                                                                                                  t)) / (averaging_time / upper)
        n = int(n)

        for i in list(range(0, n + 1)): addEquation(i, n)

        return s['stock{}'.format(n)](t)

    def forcst(self,inputstream, averaging_time, horizon, initial, t):
        memo = {"change_in_input": {}, "average_input": {}, "trend_in_input": {}, "forecast_input": {}}

        def mem(eq, t):
            """
            Internal memo for equations
            :param eq:
            :param t:
            :return:
            """
            mymemo = memo[eq]
            if t in mymemo.keys(): return mymemo[t]
            else:
                mymemo[t] = s[eq](t)
                return mymemo[t]

        s = {
            "change_in_input": lambda t: max([0, (self.memoize(inputstream,t) - mem('average_input', t)) / averaging_time]),
            "average_input": lambda t: ((self.memoize(inputstream,t)) if (t <= self.starttime) else (
                        mem("average_input", t - self.dt) + self.dt * (mem("change_in_input", t - self.dt)))),
            "trend_in_input": lambda t: (((self.memoize(inputstream,t) - self.memoize('averageInput', t)) / (
                        self.memoize('averageInput', t) * self.memoize('averagingTime', t))) if (
                        self.memoize('averageInput', t) > 0.0) else (np.nan)),
            "forecast_input": lambda t: self.memoize(inputstream,t) * (1.0 + mem("trend_in_input", t) * horizon)
        }

        return s["forecast_input"](t)

    #Helpers for Dimensions (Arrays)

    def find_dimensions(self, stock):
        stockdimensions = {}
        for dimension, values in self.dimensions.items():
            if stock in values["variables"]:
                stockdimensions[dimension] = values["labels"]

        if len(stockdimensions.keys()) == 1:
            return [stock + "[{}]".format(x) for x in stockdimensions[list(stockdimensions.keys())[0]]]

    def get_dimensions(self, equation, t):
        re_find_indices = r'\[([^)]+)\]'
        group = re.search(re_find_indices, equation).group(0).replace("[", "").replace("]", "")
        equation_basic = equation.replace(group, "").replace("[]", "")
        labels = []
        for index, elem in enumerate(group.split(",")):
            if len(elem.split(":")) > 1: # List operator
                try:
                    bounds = [int(x) for x in elem.split(":")]
                except ValueError as e:
                    logging.error(e)
                    continue
                bounds = sorted(bounds)
                if len(bounds) > 2:
                    logging.error("Too many arguments for list operator. Expecting 2, got {}".format(len(bounds)))

                labels += [list(range(bounds[0], bounds[1]+1))]

            elif elem == "*": # Star operator
                dim = self.dimensions_order[equation_basic][index]
                labels += [self.dimensions[dim]["labels"]]
            else:
                if not type(elem) is list:
                    labels += [[elem]]
                else:
                    labels += [elem]

        products = cartesian_product(labels)

        return_list = []

        for product in products:
            prod = str(product).replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("'", "").replace(" ", "")
            return_list += [self.memoize(equation_basic + "[{}]".format(prod), t)]

        return return_list


    #Access equations API

    def equation(self, equation, arg):
        return self.memoize(equation,arg)


    #Memoizer for equations. Also does most of API work

    def memoize(self, equation, arg):
        if type(equation) is float or type(equation) is int: # Fallback for values
            return equation
        if "*" in equation or ":" in equation:
            return self.get_dimensions(equation,arg)

        mymemo = self.memo[equation]

        if arg in mymemo.keys():
            return mymemo[arg]
        else:
            result = self.equations[equation](arg)
            mymemo[arg] = result

        return result


    def setDT(self, v):
        self.dt = v

    def setStarttime(self, v):
        self.starttime = v

    def setStoptime(self, v):
        self.stoptime = v
    
    def specs(self):
        return self.starttime, self.stoptime, self.dt, 'Months', 'Euler'
    