/*
 * This file is part of the GOsa project -  http://gosa-project.org
 *
 * Copyright:
 *    (C) 2010-2018 GONICUS GmbH, Germany, http://www.gonicus.de
 *
 * License:
 *    LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
 *
 * See the LICENSE file in the project's top-level directory for details.
 */

/**
 * HTML cell renderer that removes empty leading lines.
 */
qx.Class.define("gosa.ui.table.cellrenderer.Html", {
  extend: qx.ui.table.cellrenderer.Html,

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members: {
    // overridden
    _getContentHtml: function (cellInfo) {
      return cellInfo.value ? cellInfo.value.replace(/^\s*(<br\/>)*/, '') : '';
    }
  }
});
