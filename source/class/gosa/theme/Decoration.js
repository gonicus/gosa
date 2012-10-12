/* ************************************************************************

   Copyright:

   License:

   Authors:

************************************************************************ */

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
      decorator : qx.ui.decoration.Background,

      style :
      {
        backgroundImage  : "gosa/themes/default/background.png",
        backgroundRepeat : "repeat"
      }
    },

    "title-bar" :
    {
      decorator : qx.ui.decoration.Background,

      style :
      {
        backgroundImage  : "gosa/themes/default/title-bar.png",
        backgroundRepeat : "scale"
      }
    }
  }
});
