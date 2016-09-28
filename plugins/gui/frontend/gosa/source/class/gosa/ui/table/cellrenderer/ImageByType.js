/*========================================================================

 This file is part of the GOsa project -  http://gosa-project.org

 Copyright:
 (C) 2010-2016 GONICUS GmbH, Germany, http://www.gonicus.de

 License:
 LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

 See the LICENSE file in the project's top-level directory for details.

 ======================================================================== */

qx.Class.define("gosa.ui.table.cellrenderer.ImageByType", {
  extend : qx.ui.table.cellrenderer.Image,

  members : {

    _getImageInfos : function(cellInfo) {
      cellInfo['value'] = gosa.util.Icons.getIconByType(cellInfo['value'], 16);
      return this.base(arguments, cellInfo);
    }
  }
});