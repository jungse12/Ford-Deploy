var checked = localStorage.getItem("checked")
var secondButton = document.getElementById('second-life-graph-but')

window.addEventListener('load', function (event) {
  if (checked === 'new') {
    console.log('it is new')
    secondButton.disabled = true
  } else {
    console.log('it is not new')
    secondButton.disabled = false
  }
})

console.log(secondButton.disabled)

secondButton.addEventListener('click', function () {
  var x = document.getElementById('second-life-graph-container')
  if (x.style.display === 'block') {
    x.style.display = 'none'
  } else {
    x.style.display = 'block'
  }
})

if (localStorage.getItem("save-data") === null) {
  localStorage.setItem("save-data","{}")
}

function getBase64Image (img) {
  var canvas = document.createElement("canvas")
  canvas.width = img.width
  canvas.height = img.height

  var ctx = canvas.getContext("2d")
  ctx.drawImage(img, 0, 0)

  var dataURL = canvas.toDataURL("image/png")

  return dataURL.replace(/^data:image\/(png|jpg);base64,/, "")
}

var saveData = JSON.parse(localStorage.getItem('save-data'))
var saveButton = document.getElementById('save')

$(document).ready(function () {
  $('#mymodal').on('show.bs.modal', function () {
    var dict = JSON.parse(window.localStorage.getItem('save-data'))
    console.log(dict)
    for (const [key] of Object.entries(dict)) {
      var id = key + '-dict'
      if (document.getElementById(id)) {
        continue
      } else {
        var deleteImage = '<img align="right" class="delete_btn" src="../static/images/delete_button.png" id="' + key + '-img-del' + '" onclick="deleteClick(this)"/>'
        var editImage = '<img align="right" class="edit_btn" src="../static/images/edit_button.png" id="' + key + '-img-edit' + '" onclick="editClick(this)"/>'
        var string = '<div class="data-item" id="' + key + '-dict' + '">' + '<h3 class="data-header">' + key + '</h3>' + deleteImage + editImage + '</div>'
        var finalString = '<li class="data-list">' + string + '</li>'
        $('#modal-body-unlist').append(finalString)
      }
    }
  })
})

$(document).on('click', '#save-data', function (event) {
  var pv_capacity = document.getElementById('pv-capacity').textContent
  var bat_capacity = document.getElementById('bat-capacity').textContent
  var inv_capacity = document.getElementById('inv-capacity').textContent
  var cost = document.getElementById('cost').textContent
  var glob_warm_pot = document.getElementById('glob-warm-pot').textContent
  var cum_energ_demand = document.getElementById('cum-energ-demand').textContent
  var disp_thrpt = document.getElementById('disp-thrpt').textContent
  var clim_zone = document.getElementById('clim-zone').textContent
  var egrid = document.getElementById('egrid').textContent
  var state_of_charge_img = document.getElementById('state-of-charge-image')
  var state_of_charge_data = getBase64Image(state_of_charge_img)
  var pv_gen_image = document.getElementById('pv-gen-image')
  var pv_gen_data = getBase64Image(pv_gen_image)
  var elect_consump_image = document.getElementById('elect-consump-image')
  var elect_consump_data = getBase64Image(elect_consump_image)
  var name = prompt("Please enter the name of data")
  saveData = JSON.parse(localStorage.getItem('save-data'))
  if (name !== null && name !== '') {
    var dict = {
      'pv-capacity' : pv_capacity,
      'bat-capacity' : bat_capacity,
      'inv-capacity' : inv_capacity,
      'final-cost' : cost,
      'glob-warm-pot' : glob_warm_pot,
      'cum-energ-demand' : cum_energ_demand,
      'disp-thrpt': disp_thrpt,
      'clim-zone' : clim_zone,
      'egrid-sub' : egrid,
      'state-of-charge' : state_of_charge_data,
      'pv-gen' : pv_gen_data,
      'elect-consump' : elect_consump_data
    }
    var nameId = name.replace(' ', '-')
    saveData[nameId] = dict
    console.log(saveData)
    window.localStorage.setItem('save-data', JSON.stringify(saveData))
    var deleteImage = '<img align="right" class="delete_btn" src="../static/images/delete_button.png" id="' + nameId + '-img-del' + '" onclick="deleteClick(this)"/>'
    var editImage = '<img align="right" class="edit_btn" src="../static/images/edit_button.png" id="' + nameId + '-img-edit' + '" onclick="editClick(this)"/>'
    var string = '<div class="data-item" id="' + nameId + '-dict' + '">' + '<h3 class="data-header">' + name + '</h3>' + deleteImage + editImage + '</div>'
    var finalString = '<li class="data-list">' + string + '</li>'
    $('#modal-body-unlist').append(finalString)
  } else {
    return;
  }
})

function deleteClick(img) {
  var id = img.id
  var name = id.slice(0, id.indexOf('-img'))
  var divId = '#' + name + '-dict'
  var dict = JSON.parse(window.localStorage.getItem('save-data'))
  $("div").remove(divId)
  delete dict[name]
  window.localStorage.setItem('save-data', JSON.stringify(dict))
}

function editClick(img) {
  var id = img.id
  var name = id.slice(0, id.indexOf('-img'))
  var divId = '#' + name + '-dict'
  var newName = prompt('Please enter the new name of data')
  var newNameId = newName.replace(' ', '-')
  var dict = JSON.parse(window.localStorage.getItem('save-data'))

  if (newName !== null && name !== '') {
    var newDivId = newNameId + '-dict'
    var deleteNewId = newNameId + '-img-del'
    var editNewId = newNameId + '-img-edit'

    $(divId).find('h3').text(newName)
    $(divId).find('.delete_btn').attr('id', deleteNewId)
    $(divId).find('.edit_btn').attr('id', editNewId)
    $(divId).attr('id', newDivId)
    dict[newNameId] = dict[name]
    delete dict[name]
    window.localStorage.setItem('save-data', JSON.stringify(dict))
  } else {
    return
  }
}
