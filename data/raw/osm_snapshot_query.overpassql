[out:json][timeout:90];
(
  way[highway](9.7284,76.6225,9.7825,76.6765);
  node[highway~"crossing|bus_stop"](9.7284,76.6225,9.7825,76.6765);
  way[highway~"crossing|bus_stop"](9.7284,76.6225,9.7825,76.6765);
  node[amenity](9.7284,76.6225,9.7825,76.6765);
  way[amenity](9.7284,76.6225,9.7825,76.6765);
  node[shop](9.7284,76.6225,9.7825,76.6765);
  way[shop](9.7284,76.6225,9.7825,76.6765);
  node[public_transport](9.7284,76.6225,9.7825,76.6765);
);
out body geom;
