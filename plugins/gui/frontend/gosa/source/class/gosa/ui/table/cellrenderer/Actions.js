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
    _map: {
      'c': '@FontAwesome/f196', // plus
      'r': '@FontAwesome/f06e', // eye
      'w': '@FontAwesome/f044', // pencil
      'd': '@FontAwesome/f014'  // trash
    },

    // overridden
    _getContentHtml : function(cellInfo) {
      var content = "";
      cellInfo.value.forEach(function(action) {
        if (this._map[action]) {
          content += qx.bom.element.Decoration.create(this._map[action], this.getRepeat(), {
            width         : this.__imageData.width + "px",
            height        : this.__imageData.height + "px",
            display       : qx.core.Environment.get("css.inlineblock"),
            verticalAlign : "top",
            position      : "static",
            marginRight   : 3
          });
        }
      }, this);
      return content;
    },

    // overridden
    _identifyImage: function(cellinfo) {
      var imageHints =
      {
        imageWidth  : this.__imageWidth,
        imageHeight : this.__imageHeight
      };
      return imageHints;
    }
  }
});
