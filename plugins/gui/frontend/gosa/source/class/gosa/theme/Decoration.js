/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/*
#asset(gosa/themes/default/background.png)
#asset(gosa/themes/default/title-bar.png)
*/

qx.Theme.define("gosa.theme.Decoration",
{
  extend : qx.theme.indigo.Decoration,

  decorations :
  {
    "background" :
    {
      style :
      {
        backgroundImage  : "gosa/themes/default/background.png",
        backgroundRepeat : "repeat"
      }
    },

    "title-bar" :
    {
      style :
      {
        backgroundImage  : "gosa/themes/default/title-bar.png",
        backgroundRepeat : "scale"
      }
    }
  }
});
