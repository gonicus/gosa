/* ************************************************************************

   Copyright:

   License:

   Authors:

************************************************************************ */

qx.Theme.define("gosa.theme.Font",
{
  extend : qx.theme.indigo.Font,

  fonts :
  {
    "SearchResultTitle" :
      {
        size : 13,
        lineHeight : 1.4,
        bold: true,
        color: "blue",
        decoration: "underline",
        family : [ "Lucida Grande", "Tahoma", "Verdana", "Bitstream Vera Sans", "Liberation Sans" ]
      }

  }
});
