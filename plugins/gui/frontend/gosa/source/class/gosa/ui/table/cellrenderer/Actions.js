/*========================================================================

 This file is part of the GOsa project -  http://gosa-project.org

 Copyright:
 (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de

 License:
 LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

 See the LICENSE file in the project's top-level directory for details.

 ======================================================================== */

qx.Class.define("gosa.ui.table.cellrenderer.Actions", {
  extend : qx.ui.table.cellrenderer.Image,

  members: {

    // overridden
    _getContentHtml : function(cellInfo) {
      var content = "";
      var imageHints = this._identifyImage(cellInfo);
      cellInfo.value.forEach(function(action) {
        if (this._map[action]) {

          content += qx.bom.element.Decoration.create(gosa.util.Icons.getIconByAction(action), this.getRepeat(), {
            width         : imageHints.imageWidth + "px",
            height        : imageHints.imageHeight + "px",
            display       : qx.core.Environment.get("css.inlineblock"),
            verticalAlign : "top",
            position      : "static",
            marginRight   : 3
          });
        }
      }, this);
      return content;
    }
  }
});
