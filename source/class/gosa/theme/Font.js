/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Theme.define("gosa.theme.Font",
{
  extend : qx.theme.indigo.Font,

  fonts :
  {
    "underline" :
    {
      size : 12,
      family : ["Lucida Grande", "DejaVu Sans", "Verdana", "sans-serif"],
      color: "font",
      lineHeight: 1.8,
      decoration: "underline"
    },

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
