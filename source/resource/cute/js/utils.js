function getThrobber(data)
{
  var defaults = {
      color: "#000",
      size: 32,
      fade: 1000,
      rotationspeed: 0,
      lines: 14,
      strokewidth: 1.8,
      alpha: 0.4};

  if(data){
    for(var key in data){
      defaults[key] = data[key];
    }
  }

  console.log(defaults);
  var throb = new Throbber(defaults)
  return(throb);
}
