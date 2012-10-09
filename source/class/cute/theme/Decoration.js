/* ************************************************************************

   Copyright:

   License:

   Authors:

************************************************************************ */

/*
#asset(cute/themes/default/background.png)
#asset(cute/themes/default/title-bar.png)
*/

qx.Theme.define("cute.theme.Decoration",
{
  extend : qx.theme.indigo.Decoration,

  decorations :
  {
    "background" :
    {
      decorator : qx.ui.decoration.Background,

      style :
      {
        backgroundImage  : "cute/themes/default/background.png",
        backgroundRepeat : "repeat"
      }
    },

    "title-bar" :
    {
      decorator : qx.ui.decoration.Background,

      style :
      {
        backgroundImage  : "cute/themes/default/title-bar.png",
        backgroundRepeat : "scale"
      }
    }
  }
});
