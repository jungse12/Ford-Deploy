function addOptions (sel, dict) {
  for (const [key, value] of Object.entries(dict)) {
    var opt = document.createElement('option')
    opt.value = JSON.stringify(value)
    opt.text = key
    console.log(key)
    console.log(value)
    sel.appendChild(opt)
  }
};

function changeSelect (option) {
  var pv_capacity = document.getElementById('pv-capacity')
  var bat_capacity = document.getElementById('bat-capacity')
  var inv_capacity = document.getElementById('inv-capacity')
  var cost = document.getElementById('cost')
  var glob_warm_pot = document.getElementById('glob-warm-pot')
  var cum_energ_demand = document.getElementById('cum-energ-demand')
  var disp_thrpt = document.getElementById('disp-thrpt')
  var clim_zone = document.getElementById('clim-zone')
  var egrid = document.getElementById('egrid')
  var state_of_charge_img = document.getElementById('state-of-charge-image')
  var pv_gen_image = document.getElementById('pv-gen-image')
  var elect_consump_image = document.getElementById('elect-consump-image')
  if (option.value === '') {
    pv_capacity.innerText = ''
    bat_capacity.innerText = ''
    inv_capacity.innerText = ''
    cost.innerText = ''
    glob_warm_pot.innerText = ''
    cum_energ_demand.innerText = ''
    disp_thrpt.innerText = ''
    clim_zone.innerText = ''
    egrid.innerText = ''
    state_of_charge_img.src = ''
    pv_gen_image.src = ''
    elect_consump_image.src = ''
  } else {
    var dict = JSON.parse(option.value)
    pv_capacity.innerText = dict['pv-capacity']
    bat_capacity.innerText = dict['bat-capacity']
    inv_capacity.innerText = dict['inv-capacity']
    cost.innerText = dict['final-cost']
    glob_warm_pot.innerText = dict['glob-warm-pot']
    cum_energ_demand.innerText = dict['cum-energ-demand']
    disp_thrpt.innerText = dict['disp-thrpt']
    clim_zone.innerText = dict['clim-zone']
    egrid.innerText = dict['egrid-sub']
    state_of_charge_img.src = 'data:image/png;base64,' + dict['state-of-charge']
    pv_gen_image.src = 'data:image/png;base64,' + dict['pv-gen']
    elect_consump_image.src = 'data:image/png;base64,' + dict['elect-consump']
  }
}

function changeSelect2 (option) {
  var pv_capacity = document.getElementById('pv-capacity-2')
  var bat_capacity = document.getElementById('bat-capacity-2')
  var inv_capacity = document.getElementById('inv-capacity-2')
  var cost = document.getElementById('cost-2')
  var glob_warm_pot = document.getElementById('glob-warm-pot-2')
  var cum_energ_demand = document.getElementById('cum-energ-demand-2')
  var disp_thrpt = document.getElementById('disp-thrpt-2')
  var clim_zone = document.getElementById('clim-zone-2')
  var egrid = document.getElementById('egrid-2')
  var state_of_charge_img = document.getElementById('state-of-charge-image-2')
  var pv_gen_image = document.getElementById('pv-gen-image-2')
  var elect_consump_image = document.getElementById('elect-consump-image-2')
  if (option.value === '') {
    pv_capacity.innerText = ''
    bat_capacity.innerText = ''
    inv_capacity.innerText = ''
    cost.innerText = ''
    glob_warm_pot.innerText = ''
    cum_energ_demand.innerText = ''
    disp_thrpt.innerText = ''
    clim_zone.innerText = ''
    egrid.innerText = ''
    state_of_charge_img.src = ''
    pv_gen_image.src = ''
    elect_consump_image.src = ''
  } else {
    var dict = JSON.parse(option.value)
    pv_capacity.innerText = dict['pv-capacity']
    bat_capacity.innerText = dict['bat-capacity']
    inv_capacity.innerText = dict['inv-capacity']
    cost.innerText = dict['final-cost']
    glob_warm_pot.innerText = dict['glob-warm-pot']
    cum_energ_demand.innerText = dict['cum-energ-demand']
    disp_thrpt.innerText = dict['disp-thrpt']
    clim_zone.innerText = dict['clim-zone']
    egrid.innerText = dict['egrid-sub']
    state_of_charge_img.src = 'data:image/png;base64,' + dict['state-of-charge']
    pv_gen_image.src = 'data:image/png;base64,' + dict['pv-gen']
    elect_consump_image.src = 'data:image/png;base64,' + dict['elect-consump']
  }
}

window.addEventListener('load', function (event) {
  var sel1 = document.getElementById('savedData1')
  var sel2 = document.getElementById('savedData2')
  if (window.localStorage.getItem('save-data') === null) {
    window.alert('User must save at least one data to compare')
  } else {
    var savedData = JSON.parse(window.localStorage.getItem('save-data'))
    addOptions(sel1, savedData)
    addOptions(sel2, savedData)
  }
})

/*
testButton.addEventListener('click', function () {
  var img = document.getElementById('testImage')
  img.src = 'data:image/png;base64,' + dataImage
})
*/
