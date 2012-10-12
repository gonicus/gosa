/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

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

  var throb = new Throbber(defaults);
  return(throb);
}
