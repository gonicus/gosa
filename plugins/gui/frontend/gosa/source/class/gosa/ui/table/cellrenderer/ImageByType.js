/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

qx.Class.define("gosa.ui.table.cellrenderer.ImageByType", {
  extend : qx.ui.table.cellrenderer.Image,

  members: {
    // overridden
    _getContentHtml : function(cellInfo)
    {
      var content = this.base(arguments, cellInfo);
      content = content.replace("display: "+qx.core.Environment.get("css.inlineblock")+";", "");
      return content;
    },

    // overridden
    _identifyImage : function(cellInfo)
    {
      var imageHints = this.base(arguments, cellInfo);

      if (cellInfo.value !== "") {
        imageHints.url = gosa.util.Icons.getIconByType(cellInfo.value, 16);
      }

      return imageHints;
    }
  }
});
