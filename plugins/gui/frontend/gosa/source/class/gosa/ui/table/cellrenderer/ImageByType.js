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
      var content = "<div></div>";

      // set image
      if (this.__imageData.url) {
        content = qx.bom.element.Decoration.create(
          this.__imageData.url,
          this.getRepeat(),
          {
            width: this.__imageData.width + "px",
            height: this.__imageData.height + "px",
            verticalAlign: "top",
            position: "static"
          });
      };

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
