[out:json][timeout:90];
(
  way[highway](9.7229,76.6170,9.7880,76.6820);
  node[highway~"crossing|bus_stop"](9.7229,76.6170,9.7880,76.6820);
  way[highway~"crossing|bus_stop"](9.7229,76.6170,9.7880,76.6820);
  node[amenity](9.7229,76.6170,9.7880,76.6820);
  way[amenity](9.7229,76.6170,9.7880,76.6820);
  node[shop](9.7229,76.6170,9.7880,76.6820);
  way[shop](9.7229,76.6170,9.7880,76.6820);
  node[public_transport](9.7229,76.6170,9.7880,76.6820);
);
(._;>;);
out body geom;
