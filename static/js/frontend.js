(function() {

OpenLayers.Control.Click = OpenLayers.Class(OpenLayers.Control, {
    mapClicked: function() {},

    initialize: function(mapClicked, options) {
        OpenLayers.Control.prototype.initialize.apply(this, [options]);
        if(mapClicked) this.mapClicked = mapClicked;
        this.handler = new OpenLayers.Handler.Click(
            this, {'click': this.trigger});
    },

    trigger: function(e) {
        this.mapClicked(e.xy);
    }
});

window.M = {};
M.proj_wgs1984 = new OpenLayers.Projection("EPSG:4326");
M.proj_mercator = new OpenLayers.Projection("EPSG:900913");
M.project = function(point) {
  return point.clone().transform(M.proj_wgs1984, M.proj_mercator);
};
M.reverse_project = function(point) {
  return point.clone().transform(M.proj_mercator, M.proj_wgs1984);
};

M.init_map = function() {
  M.map = new OpenLayers.Map({
    'div': "map",
    'controls': [
      new OpenLayers.Control.Navigation(),
      new OpenLayers.Control.ZoomPanel(),
      new OpenLayers.Control.Attribution()
    ]});
  M.map.addControl(new OpenLayers.Control.TouchNavigation({
    'dragPanOptions': {'enableKinetic': true}
  }));
  M.map.addLayer(new OpenLayers.Layer.OSM());
  M.map.setCenter(M.project(new OpenLayers.LonLat(26.10, 44.43)), 13);
}

M.center_to_gps = function() {
  window.navigator.geolocation.getCurrentPosition(function(position){
      var lon = position.coords.longitude, lat = position.coords.latitude;
      var center = new OpenLayers.LonLat(lon, lat);
      M.map.setCenter(M.project(center), 16);
      $('#poi-form form input[name=lat]').val(lat);
      $('#poi-form form input[name=lon]').val(lon);
  });
}

M.enable_adding_points = function() {
  var points_layer = new OpenLayers.Layer.Vector("Points");
  M.map.addLayer(points_layer);
  var add_point = new OpenLayers.Control.Click(function(xy) {
    var lonlat = M.reverse_project(M.map.getLonLatFromViewPortPx(xy));
    console.log('clicked on', lonlat.lon, lonlat.lat);
  });
  M.map.addControl(add_point);
  add_point.activate();
};

})();
