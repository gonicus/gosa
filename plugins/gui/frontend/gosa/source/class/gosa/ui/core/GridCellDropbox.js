/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
* Droppable placesholder for the dashboard grid. Users can drop widgets on these items to move them around in the grid
*/
qx.Class.define("gosa.ui.core.GridCellDropbox", {
  extend : qx.ui.core.Widget,

  /*
  *****************************************************************************
     CONSTRUCTOR
  *****************************************************************************
  */
  construct : function() {
    this.base(arguments);

    this.addListener("dragover", this._onDragOver, this);
    this.addListener("dragleave", this._onDragLeave, this);
    this.addListener("drop", this._onDrop, this);
  },

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {
    appearance: {
      refine: true,
      init: "gosa-droppable"
    },

    droppable: {
      refine: true,
      init: true
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    _onDragOver: function() {
      this.addState("hovered");
    },
    _onDragLeave: function() {
      this.removeState("hovered");
    },
    _onDrop: function(ev) {
      this.removeState("hovered");
      qx.event.message.Bus.dispatchByName("gosa.dashboard.drop", {
        widget: ev.getRelatedTarget(),
        props:  this.getLayoutProperties()
      });
    }
  }
});