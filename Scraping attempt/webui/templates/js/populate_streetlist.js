function nbhoodSelections() {
  var selectList = "<select name='selected-street'>";
  var nbhoods = {{ neighborhood_list|tojson }};
  for (var x = 0; x < nbhoods.length; x++) {
    selectList += "<option>" + nbhoods[x] + "</option>";
  }
  selectList += "</select>";
  $('#neighborhood-dropdown').html(selectList);

  // Disable address form if there are no neighborhoods in dropdown
  if (nbhoods.length < 1) {
  	console.log($('#neighborhood-dropdown'));
    $("#input-address-range :input").attr('disabled', true);
  }
}

$(document).ready(function() {
  nbhoodSelections();
});