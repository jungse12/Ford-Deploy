var climateZone = 0;
var zone_list;
var fileUpload;
var fileCheck = 0;

function updateTextInput(val, input_Id) {
    document.getElementById(input_Id).value = val;

    if (input_Id === 'fast-charger-watt') {
        document.getElementById('bat-lower-limit').value = val;
    }
}

function updateSliderValue(val, slider_Id) {
    document.getElementById(slider_Id).value = val;

    if (slider_Id === 'fast-charger-watt-slider') {
        document.getElementById('bat-lower-limit').value = val;
    }
}

function netMetering() {
    if(document.getElementById("net-metering").checked === true) {
        document.getElementById("net-metering").value = 1;
        document.getElementById("feed-in-tariff").classList.add('disabled');
        document.getElementById("btn-feed-in-tariff").classList.remove('btn-outline-success');
        document.getElementById("btn-feed-in-tariff").classList.add('btn-outline-secondary');
        document.getElementById("btn-feed-in-tariff").style.opacity = "0.5";
    }
    else {
        document.getElementById("net-metering").value = 0;
        document.getElementById("feed-in-tariff").classList.remove('disabled');
        document.getElementById("btn-feed-in-tariff").classList.remove('btn-outline-secondary');
        document.getElementById("btn-feed-in-tariff").classList.add('btn-outline-success');
        document.getElementById("btn-feed-in-tariff").style.opacity = "1";
    }
}

function feedTariff() {
    if(document.getElementById("feed-in-tariff").checked === true) {
        document.getElementById("feed-in-tariff").value = 1;
        document.getElementById("feed-in-tariff-rate").readOnly = false;
        document.getElementById("net-metering").classList.add('disabled');
        document.getElementById("btn-net-metering").classList.remove('btn-outline-success');
        document.getElementById("btn-net-metering").classList.add('btn-outline-secondary');
        document.getElementById("btn-net-metering").style.opacity = "0.5";
    }
    else {
        document.getElementById("feed-in-tariff").value = 0;
        document.getElementById("feed-in-tariff-rate").readOnly = true;
        document.getElementById("net-metering").classList.remove('disabled');
        document.getElementById("btn-net-metering").classList.remove('btn-outline-secondary');
        document.getElementById("btn-net-metering").classList.add('btn-outline-success');
        document.getElementById("btn-net-metering").style.opacity = "1";
    }
}

function updateOptOptions(currentOption) {
    
    var radioItems = ['minimize-cost','carbn-ftprnt','cum-dem'];
    if (currentOption.checked === true) {
        currentOption.value = 1;
    } else {
        currentOption.value = 0;
    }
    for (var i = 0; i < radioItems.length; i++) {
        if (currentOption.id !== radioItems[i]) {
            document.getElementById(radioItems[i]).value = 0;
        }
    }
}


function showAlert(id) {
    var name = '#' + id
    if (id === 'elec-alert') {
        $(name).fadeIn( 300 ).delay( 1500 ).fadeOut( 400 );
    } else {
        if (document.getElementById('zipcode').length > 0 && document.getElementById('utility-matrix-name1').length > 0) {
            $(name).fadeIn( 300 );
        }
    }
}

var geo, weather, utility;

function callGoogleAPI() {
    var zipcode = document.getElementById('zipcode').value;
    var state = document.getElementById('state').value;
    const weatherData = document.getElementById('weather-data');
    const weatherDataMsg = document.getElementById('weather-data-msg');
    const utilityData = document.getElementById('utility-data');
    const utilityDataMsg = document.getElementById('utility-data-msg');
    const locationErrorMsg = document.getElementById('location-error-msg');
    var latitudeInput = document.getElementById('lat');
    var longitudeInput = document.getElementById('long');

    //console.log(tilt);

    var lat = 0;
    var lng = 0;

    if (zipcode == "" && state == "") {
        locationErrorMsg.innerHTML = "Please, enter your zipcode and state.";
        return;
    }
    else if (zipcode == "") {
        locationErrorMsg.innerHTML = "Please, enter your zipcode.";
        return;
    }
    else if (state == "") {
        locationErrorMsg.innerHTML = "Please, enter your state.";
        return;
    }
    else {
        locationErrorMsg.innerHTML = "";
    }

    fetch('https://maps.googleapis.com/maps/api/geocode/json?address='+zipcode+'&key=AIzaSyCOvVLr8XM0VD0CVsfqAkplqHYquFYIQw4')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            console.log(data);
            geo = data;
            var result = data.results;
            var length = data.results.length;
            if (length > 0) {
                lat = result[0].geometry.location.lat;
                latitudeInput.value = lat;
                lng = result[0].geometry.location.lng;
                longitudeInput.value = lng;
                $('input[name="tilt-value"]').val(lat);

            }
            else {
                locationErrorMsg.innerHTML = "Cannot find a location";
            }
            
            return fetch('https://developer.nrel.gov/api/solar/nsrdb_data_query.json?api_key=YeWSwIxO37j4AHerp8lyZhnBajXEpTBYI1bAyiC5&lat='+lat+'&lon='+lng);
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            console.log("this is weather: " + data)
            weather = data;
            var result = data.outputs;
            var found = false;
            for (var i = 0; i < result.length; i++) {
                link = result[i]["links"][0]["link"].replace("yourapikey", "YeWSwIxO37j4AHerp8lyZhnBajXEpTBYI1bAyiC5");
                if (link.includes("tmy3") == true) {
                    weatherDataMsg.innerHTML = "Weather data: ";
                    weatherData.innerHTML = "download";
                    weatherData.href = link;
                    found = true;
                }
            }
            if (found == false) {
                weatherDataMsg.innerHTML = "Weather file is not found.";
                weatherData.innerHTML = "";
                weatherData.href = "";
            }
            return fetch('https://api.openei.org/utility_rates?version=3&format=json&api_key=oZ2QzF0Y9AmZ6ox5EhCVElgphCikPgB996W2uflv&lat='+lat+'&lon='+lng+'&sector=Residential&co_limit=1&detail=full&approved=true');
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            console.log("this is data:" + data);
            utility = data;
            var result = data.items;
            var options = [];
            for (var i = 0; i < result.length; i++) {
                options.push([result[i].name, result[i].uri]);
            }
            if (lat == 0 && lng == 0) {
                utilityDataMsg.innerHTML = "Utility rate is not found.";
                utilityData.innerHTML = "";
            }
            else {

                var detailButton = ' <input type="button" id="custom-detail-btn" value="Details" onclick="openDetails()">';
                var tableSetUpWd = '<table style="font-size:80%"><tr><th><th>Jan<th>Feb<th>Mar<th>Apr<th>May<th>Jun<th>Jul<th>Aug<th>Sep<th>Oct<th>Nov<th>Dec</tr>'
                var tableSetUpWe = '<table style="font-size:80%"><tr><th><th>Jan<th>Feb<th>Mar<th>Apr<th>May<th>Jun<th>Jul<th>Aug<th>Sep<th>Oct<th>Nov<th>Dec</tr>'

                var time = 11;
                var zone = 'pm';
                var zoneBool = false;
                for (var i = 0; i < 24; i++){
                    var tr = '<tr>';
                    if (time === 0) {
                        time = 12;
                        zoneBool = true;
                    }
                    var headTd = '<td>' + time + zone;
                    var janTd = '<td>' + '<input type="text" class="detail-input" value="0.0" ' +  'id="0-' + time + zone + '-wd"/>';
                    var febTd = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="1-' + time + zone + '-wd"/>';
                    var marTd = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="2-' + time + zone + '-wd"/>';
                    var aprTd = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="3-' + time + zone + '-wd"/>';
                    var mayTd = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="4-' + time + zone + '-wd"/>';
                    var junTd = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="5-' + time + zone + '-wd"/>';
                    var julTd = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="6-' + time + zone + '-wd"/>';
                    var augTd = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="7-' + time + zone + '-wd"/>';
                    var sepTd = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="8-' + time + zone + '-wd"/>';
                    var octTd = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="9-' + time + zone + '-wd"/>';
                    var novTd = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="10-' + time + zone + '-wd"/>';
                    var decTd = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="11-' + time + zone + '-wd"/>';

                    var headTdE = '<td>' + time + zone;
                    var janTdE = '<td>' + '<input type="text" class="detail-input" value="0.0" ' +  'id="0-' + time + zone + '-we"/>';
                    var febTdE = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="1-' + time + zone + '-we"/>';
                    var marTdE = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="2-' + time + zone + '-we"/>';
                    var aprTdE = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="3-' + time + zone + '-we"/>';
                    var mayTdE = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="4-' + time + zone + '-we"/>';
                    var junTdE = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="5-' + time + zone + '-we"/>';
                    var julTdE = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="6-' + time + zone + '-we"/>';
                    var augTdE = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="7-' + time + zone + '-we"/>';
                    var sepTdE = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="8-' + time + zone + '-we"/>';
                    var octTdE = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="9-' + time + zone + '-we"/>';
                    var novTdE = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="10-' + time + zone + '-we"/>';
                    var decTdE = '<td>' + '<input type="text" class="detail-input" value="0.0"' +  'id="11-' + time + zone + '-we"/>';
                    time -= 1;
                    if (zoneBool === true && time === 11) {
                        zone = 'am';
                    }
                    tableSetUpWd += tr + headTd + janTd + febTd + marTd + aprTd + mayTd + junTd + julTd + augTd + sepTd + octTd + novTd + decTd;
                    tableSetUpWe += tr + headTdE + janTdE + febTdE + marTdE + aprTdE + mayTdE + junTdE + julTdE + augTdE + sepTdE + octTdE + novTdE + decTdE;
                    //tr += ''
                }
                tableSetUpWd += '</table>'
                tableSetUpWe += '</table>'
                //console.log(tableSetUp);
                var detailDiv = '<div id="detail-div" style="display:none">' + '<div>' + '<div class="text-center">Weekday</div>' + tableSetUpWd + '</div>' + '<div>' + '<div class="text-center" style="padding-top: 5px">Weekend</div>' + tableSetUpWe + '</div>'+ '</div>'
                utilityDataMsg.innerHTML = "Utility rate: <br>";
                optionList = '<div class="radio" style="display:inline"><label><input type="radio" name="utility-options" value="custom">' + 'User\'s custom rate input' + detailButton + detailDiv + '</div>';
                utilityData.innerHTML += optionList;
                for (var i = 0; i < options.length; i++) {
                    optionList = '<div class="radio"><label><input type="radio" name="utility-options" value="'+ i +'">' + options[i][0] + '<a href="' + options[i][1] + '" target="_blank"> Preview</a></label></div>';
                    utilityData.innerHTML += optionList;
                }
                options.length = 0;
            }
            return fetch('https://maps.googleapis.com/maps/api/timezone/json?location='+lat+','+lng + '&timestamp=1458000000&key=AIzaSyCOvVLr8XM0VD0CVsfqAkplqHYquFYIQw4')
        })
        .then(function(response){
            return response.json();
        })
        .then(function(data) {
            var timezone = data['rawOffset'] / 3600
            document.getElementById('t_z').value = 'GMT' + timezone;
        })
        .catch(function(error) {
            console.log('error');
        })
}

function openDetails() {
    var x = document.getElementById('detail-div');
    if (x.style.display === 'block') {
        x.style.display = 'none'
    } else {
        x.style.display = 'block'
    }
}

function resetAPIdata() {
    const weatherData = document.getElementById('weather-data');
    const weatherDataMsg = document.getElementById('weather-data-msg');
    const utilityData = document.getElementById('utility-data');
    const utilityDataMsg = document.getElementById('utility-data-msg');
    const locationErrorMsg = document.getElementById('location-error-msg');

    weatherDataMsg.innerHTML = "";
    weatherData.innerHTML = "";
    weatherData.href = "#";
    utilityData.innerHTML = "";
    utilityDataMsg.innerHTML = "";
    locationErrorMsg.innerHTML = "";
}

function zeros(dimensions) {
    var array = [];

    for (var i = 0; i < dimensions[0]; ++i) {
        array.push(dimensions.length == 1 ? 0 : zeros(dimensions.slice(1)));
    }

    return array;
}

localStorage.setItem("checked","new");

function toggleSecondBatteryLife(flag) {
    var x = document.getElementById('second-battery-life');
    var y = document.getElementById("second-life-battery-container");
    var bat_cost = document.getElementById('bat-cost');
    var bat_cost_slider = $('#bat-cost-slider');
    var bat_effi = document.getElementById('bat-effi');
    var bat_effi_slider = $('#bat-effi-slider');
    var bat_warranty = document.getElementById('bat-warranty');
    var bat_warranty_slider = $('#bat-warranty-slider');

    if (flag == 1) {
        y.style.display = "block";
        bat_cost.readOnly = true;
        //bat_cost.prop("disabled", true);
        bat_cost_slider.prop("disabled",true);
        bat_effi.readOnly = true;
        bat_effi_slider.prop("disabled",true);
        bat_warranty.readOnly = true;
        bat_warranty_slider.prop("disabled",true);
        localStorage.setItem("checked","second");
        //$(bat_cost_slider).addClass('hover-disabled-cursor');
        //$("#slider::-moz-range-thumb").style.setProperty("cursor","not-allowed");
    } else {
        y.style.display = "none";
        bat_cost.readOnly = false;
        bat_cost_slider.prop("disabled",false);
        bat_effi.readOnly = false;
        bat_effi_slider.prop("disabled",false);
        bat_warranty.readOnly = false;
        bat_warranty_slider.prop("disabled",false);
        localStorage.setItem("checked","new");
    }

};

function secondLifeBatteryOption() {
    var selectBox = document.getElementById('ouput-model');
    var selectedValue = selectBox.options[selectBox.selectedIndex].value;
    var laborCost = document.getElementById('labor-cost');
    var electCost = document.getElementById('elect-cost');
    var transDist = document.getElementById('trans-distance');

    if (selectedValue == 'eol-remanufact-recycle') {
        laborCost.readOnly = false;
        electCost.readOnly = false;
        transDist.readOnly = false;
    } else if (selectedValue == 'pot-labor-cost') {
        laborCost.readOnly = true;
        electCost.readOnly = false;
        transDist.readOnly = false;
    } else if (selectedValue == 'pot-elect-cost') {
        laborCost.readOnly = false;
        electCost.readOnly = true;
        transDist.readOnly = false;
    } else if (selectedValue == 'pot-trans-distance') {
        laborCost.readOnly = false;
        electCost.readOnly = false;
        transDist.readOnly = true;
    }
};
$(document).ready(function() {
    $('#custom-file').on('change', function(e) {
        var file = e.target.files[0];
        // input canceled, return
        if (!file) return;
        var FR = new FileReader();
        FR.onload = function(e) {
            var data = new Uint8Array(e.target.result);
            var workbook = XLSX.read(data, {type: 'array'});
            var firstSheet = workbook.Sheets[workbook.SheetNames[0]];
            
            // header: 1 instructs xlsx to create an 'array of arrays'
            var result = XLSX.utils.sheet_to_json(firstSheet, { header: 1 });
            fileUpload = [].concat.apply([],result)
            fileCheck = 1;
            //fileUpload = Object.keys(obj).map((key) => [Number(key), obj[key]]);
            // data preview
            //var output = document.getElementById('result');
            //output.innerHTML = JSON.stringify(result, null, 2);
        };
        FR.readAsArrayBuffer(file);
    });
    $('#loadData').on('click', function(e) {
        e.preventDefault();
        var zipcode = $('#zipcode').val();
        var state = $('#state').val();
        var year = $('#year').val();

        req = $.ajax({
            url:'load',
            type: 'POST',
            data: {
                file: JSON.stringify(fileUpload),
                filecheck: fileCheck,
                zipcode: zipcode,
                state: state,
                year: year,
                csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val()
            },
            success: function(data){
                console.log("after loaded" + data);
                document.getElementById('Elec-GWP').value = data[0]['fields']['gwp'];
                document.getElementById('Elec-CED').value = data[1]['fields']['ced'];
                climateZone = data[2]['fields']['climate_zone'];
            }
        });
    });
    $('#chooseButton').on('click', function(e) {
        const weatherData = document.getElementById('weather-data');
        const weatherDataMsg = document.getElementById('weather-data-msg');
        const utilityData = document.getElementById('utility-data');
        const utilityDataMsg = document.getElementById('utility-data-msg');
        const locationErrorMsg = document.getElementById('location-error-msg');

        // Check which option the user chose.
        var radio = document.querySelector('input[name="utility-options"]:checked').value;
        //console.log(radio);
        if (radio === 'custom') {
            var data_values_WD = Array.from(Array(24), _ => Array(12).fill(0));
            var data_values_WE = Array.from(Array(24), _ => Array(12).fill(0));

            var totalRate = [];
            var timeCustom = 12;
            var zoneCustom = 'am';
            for (var i = 0; i < 24; i++) {
                for (var j =0; j < 12; j++) {
                    var idWd = j + '-' + timeCustom + zoneCustom + '-wd';
                    var idWe = j + '-' + timeCustom + zoneCustom + '-we';
                    var valWd = document.getElementById(idWd).value;
                    var valWe = document.getElementById(idWe).value;
                    data_values_WD[i][j] = parseFloat(valWd) * 100;
                    data_values_WE[i][j] = parseFloat(valWe) * 100;
                    totalRate.push(parseFloat(valWd));
                    totalRate.push(parseFloat(valWe));
                }
                timeCustom += 1;
                if (timeCustom === 13) {
                    timeCustom = 1;
                }
                if (timeCustom === 12 && zoneCustom === 'am') {
                    zoneCustom = 'pm';
                }
            }

            z_min = Math.min.apply(Math, totalRate) * 100;
            z_max = Math.max.apply(Math, totalRate) * 100;
        } else {
            // Get utility data based on the user's choice.
            var selected = utility.items[radio];
            
            var name1 = selected.utility;
            var name2 = selected.name;
            document.getElementById('utility-matrix-name1').innerHTML = name1;
            document.getElementById('utility-matrix-name2').innerHTML = name2;
            console.log(selected);

            // Forming a matrix
            var lifetime = document.getElementById('proj-lifetime').value;
            var energyRatesData = [];
            var energyRateStructure = [];
            var energyWeekdaySchedule = [];
            var energyWeekendSchedule = [];
            for (var i = 0; i < selected.energyratestructure.length; i++) {
                energyRateStructure.push(selected.energyratestructure[i][0].rate);
            }
            energyWeekdaySchedule = selected.energyweekdayschedule;
            energyWeekendSchedule = selected.energyweekendschedule;

            console.log(energyRateStructure);

            z_min = Math.min.apply(Math, energyRateStructure) * 100;
            z_max = Math.max.apply(Math, energyRateStructure) * 100;

            console.log(z_min + ' ' + z_max);

            var defaultPlotlyConfiguration = {
                modeBarButtonsToRemove: ['sendDataToCloud', 'autoScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'lasso2d', 'select2d'],
                displaylogo: false,
                showTips: true,
                responsive: true
            };
            var data_values_WD = Array.from(Array(24), _ => Array(12).fill(0));
            for (var i = 0; i < energyWeekdaySchedule.length; i++) {
                for (var j = 0; j < energyWeekdaySchedule[0].length; j++) {
                    data_values_WD[j][i] = energyRateStructure[energyWeekdaySchedule[i][j]] * 100;
                }
            }

            var data_values_WE = Array.from(Array(24), _ => Array(12).fill(0));
            for (var i = 0; i < energyWeekendSchedule.length; i++) {
                for (var j = 0; j < energyWeekendSchedule[0].length; j++) {
                    data_values_WE[j][i] = energyRateStructure[energyWeekendSchedule[i][j]] * 100;
                }
            }
        }
        //onsole.log(data_values_WD);
        // Create a 2D matrix for data calculation purpose
        var dayInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
        var dayInMonthC = [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365];
        var touRateList = []
        for (var i = 0; i < 24; i++) {
            tmpList = [];
            //console.log("number: " + i);
            for (var month = 0; month < dayInMonth.length; month++){
                monthlyDay = dayInMonth[month];
                for (var j = 0; j < monthlyDay; j++) { //NEED TO SEND ARRAY WITH 8760 DATAS
                    // Weekday
                    if ((j % 7) < 5) {
                        tmpList.push(data_values_WD[i][month]/100);
                    }
                    // Weekend
                    else {
                        tmpList.push(data_values_WE[i][month]/100);
                    }
                }
            }
            touRateList.push(tmpList);
        }

        var layoutWeekday = {
            title: "Weekday",
            margin: {
                l: 50,
                r: 10,
                b: 60,
                t: 50,
            }
        }
        var layoutWeekend = {
            title: "Weekend",
            margin: {
                l: 50,
                r: 10,
                b: 60,
                t: 50,
            }
        }

        var dataWeekday = [
            {
                z: data_values_WD,
                x: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                y: ["12 am", "1 am", "2 am", "3 am", "4 am", "5 am", "6 am", "7 am", "8 am", "9 am", "10 am", "11 am", "12 pm", "1 pm", "2 pm", "3 pm", "4 pm", "5 pm", "6 pm", "7 pm", "8 pm", "9 pm", "10 pm", "11 pm"],
                zmin: z_min,
                zmax: z_max,
                xgap: 1,
                ygap: 1,
                colorscale: 'Portland',
                type: 'heatmap'
            }
        ];

        var dataWeekend = [
            {
                z: data_values_WE,
                x: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                y: ["12 am", "1 am", "2 am", "3 am", "4 am", "5 am", "6 am", "7 am", "8 am", "9 am", "10 am", "11 am", "12 pm", "1 pm", "2 pm", "3 pm", "4 pm", "5 pm", "6 pm", "7 pm", "8 pm", "9 pm", "10 pm", "11 pm"],
                colorscale: 'Portland',
                zmin: z_min,
                zmax: z_max,
                xgap: 1,
                ygap: 1,
                type: 'heatmap'
            }
        ];
        console.log(data_values_WD); 
        var test = 1;
        Plotly.newPlot('weekday', dataWeekday, layoutWeekday, defaultPlotlyConfiguration);
        Plotly.newPlot('weekend', dataWeekend, layoutWeekend, defaultPlotlyConfiguration);
        e.preventDefault();
        var category = document.querySelector('input[name="system-app"]:checked').value;
        req = $.ajax({
            url:'matrixDatabase',
            type: 'POST',
            data: {
                filecheck: fileCheck,
                //rateList: JSON.stringify(touRateList),
                system_app: category,
                climate_zone: climateZone,
                csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val()
            },
            success: function(data){
                zone_list = JSON.parse(data);
                if (category === 'fast-charger') {
                    var fastChargerRate = document.getElementById('fast-charger-watt').value / 100;
                    for (var i = 0; i < zone_list.length; i++) {
                        zone_list[i] = zone_list[i] * fastChargerRate;
                    }
                } else if (category === 'home-charger') {
                    console.log(data_values_WD)
                    var indexValues;
                    var wdIndex, weIndex;
                    var totalDay = 0;
                    console.log("totalDaY0: " + zone_list.slice(0,360))
                    for (var indexMonth = 0; indexMonth < 12; indexMonth++) {
                        indexValues = lowestRate(data_values_WD, data_values_WE, indexMonth);
                        wdIndex = indexValues[0];
                        weIndex = indexValues[1];
                        console.log("INDEX: " + wdIndex + ' ' + weIndex)
                        for (var indexDay = 0; indexDay < dayInMonth[indexMonth]; indexDay++) { //NEED TO SEND ARRAY WITH 8760 DATAS
                            // Weekday
                            var indexHour = totalDay * 24;
                            if ((indexDay%7) < 5) {
                                zone_list[indexHour+wdIndex] += 0.08;
                                zone_list[indexHour+wdIndex+1] += 0.08;
                            }
                            // Weekend
                            else {
                                zone_list[indexHour+weIndex] += 0.08;
                                zone_list[indexHour+weIndex+1] += 0.08;
                            }
                            totalDay += 1;
                        }
                    }
                    //console.log("totalDaY: " + zone_list.slice(0,360));
                }
                $.ajax({
                    url:'assignDatabase',
                    type: 'POST',
                    data: {
                        rateList: JSON.stringify(touRateList),
                        zoneList: JSON.stringify(zone_list),
                        csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val()
                    },
                    success: function(data){
                        //zone_list = JSON.parse(data);
                    }
                });
            }
        });
        weatherDataMsg.innerHTML = "";
        weatherData.innerHTML = "";
        weatherData.href = "#";
        utilityData.innerHTML = "";
        utilityDataMsg.innerHTML = "";
        locationErrorMsg.innerHTML = "";
    });
    $("input[name='system-app']").change(function(){
        var x = document.getElementById('fast-charger-div')
        if (this.value === 'fast-charger'){
            document.getElementById('pv-lower-limit').value = 0;
            document.getElementById('pv-upper-limit').value = 50;
            document.getElementById('bat-lower-limit').value = document.getElementById('fast-charger-watt').value;
            document.getElementById('bat-upper-limit').value = 1000;
            if (x.style.display === 'block') {
                x.style.display = 'none'
            } else {
                x.style.display = 'block'
            }
        } else {
            x.style.display = 'none'
        }
        if (this.value === 'home-ESS' && this.value === 'micro-ESS') {
            document.getElementById('pv-lower-limit').value = 0;
            document.getElementById('pv-upper-limit').value = 500;
            document.getElementById('bat-lower-limit').value = 0;
            document.getElementById('bat-upper-limit').value = 500;
        }
        if (this.value === 'home-charger') {
            document.getElementById('pv-lower-limit').value = 5;
            document.getElementById('pv-upper-limit').value = 5;
            document.getElementById('bat-lower-limit').value = 0;
            document.getElementById('bat-upper-limit').value = 20;
        }
    });
});



function lowestRate(data_values_WD, data_values_WE, month){
    var wdIndex = 18;
    var weIndex = 18;
    var weValue = data_values_WE[18][month];
    var wdValue = data_values_WD[18][month];

    for (var i = 19; i < 23; i++) {
        if (wdValue > data_values_WD[i][month]) {
            wdValue = data_values_WD[i][month];
            wdIndex = i;
        }
        if (weValue > data_values_WE[i][month]) {
            weValue = data_values_WE[i][month];
            weIndex = i;
        }
    }
    if (wdIndex === 18) {
        wdIndex = 20;
    }
    if (weIndex === 18) {
        weIndex = 20;
    }
    return [wdIndex, weIndex];


}
