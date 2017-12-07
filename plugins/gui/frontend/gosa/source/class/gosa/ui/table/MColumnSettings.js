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
qx.Mixin.define('gosa.ui.table.MColumnSettings', {
  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members: {
    _applyColumnSettings: function(table, settings) {
      var tcm = table.getTableColumnModel();
      for (var column in settings.renderers) {
        var clazz = qx.Class.getByName(settings.renderers[column].class);
        var renderer;
        if (settings.renderers[column].hasOwnProperty("params")) {
          var f = clazz.bind.apply(clazz, settings.renderers[column].params);
          renderer = new f();
        } else {
          renderer = new clazz();
        }
        tcm.setDataCellRenderer(parseInt(column), renderer);
      }
      var resizeBehavior = tcm.getBehavior();
      for (var column in settings.widths) {
        resizeBehavior.setWidth(parseInt(column), settings.widths[column]);
      }
    } 
  }
});
