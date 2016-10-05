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

  /*
   *****************************************************************************
   CONSTRUCTOR
   *****************************************************************************
   */


  /**
   * @param height {Integer?16} The height of the image. The default is 16.
   * @param width {Integer?16} The width of the image. The default is 16.
   */
  construct : function(width, height)
  {
    this.base(arguments);

    if (width) {
      this._imageWidth = width;
    }

    if (height) {
      this._imageHeight = height;
    }
  },

  members: {
    _imageHeight : 16,
    _imageWidth : 16,

    // overridden
    _identifyImage : function(cellInfo)
    {
      var imageHints =
      {
        imageWidth  : this._imageWidth,
        imageHeight : this._imageHeight
      };
      return imageHints;
    },

    // overridden
    _getContentHtml : function(cellInfo) {
      var content = "";
      cellInfo.value.forEach(function(action) {
        var icon = gosa.util.Icons.getIconByAction(action);

        if (icon) {
          content += qx.bom.element.Decoration.create(icon, this.getRepeat(), {
            width         : this._imageWidth + "px",
            height        : this._imageHeight + "px",
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
