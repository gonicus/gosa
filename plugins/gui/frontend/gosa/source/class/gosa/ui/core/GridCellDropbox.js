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

    var bounds = this.getBounds();
    if (!bounds) {
      this.addListenerOnce("appear", function() {
        this.__gridLayout = this.getLayoutParent().getLayout();
      }, this);
    } else {
      this.__gridLayout = this.getLayoutParent().getLayout();
    }

    this.setBuddyArea(new qx.data.Array());
    this.addListener("changeHovered", function(ev) {
      if (ev.getData()) {
        this.addState("hovered");
      } else {
        this.removeState("hovered");
      }
    }, this);
  },

  /*
  *****************************************************************************
     STATICS
  *****************************************************************************
  */
  statics : {
    __startBuddy: null,

    setStartBuddy: function(start) {
      if (this.__startBuddy === start) {
        return;
      }
      if (this.__startBuddy) {
        // reset the old one
        this.__startBuddy.setHovered(false);
        this.__startBuddy.getBuddyArea().forEach(function(widget) {
          widget.resetStartBuddy();
        }, this);
        this.__startBuddy.getBuddyArea().removeAll();
      }
      this.__startBuddy = start;
    }
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
    },

    /**
     * Temporary drop target for currently dragged the multi-colspan item
     */
    startBuddy: {
      check: "gosa.ui.core.GridCellDropbox",
      nullable: true,
      apply: "_applyStartBuddy"
    },

    /**
     * Related cells to a StartBuddy
     */
    buddyArea: {
      check: "qx.data.Array"
    },

    hovered: {
      check: "Boolean",
      init: false,
      event: "changeHovered"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    __gridLayout: null,

    _applyStartBuddy: function(value, old) {
      if (old) {
        old.removeRelatedBindings(this);
      }
      if (value) {
        value.bind("hovered", this, "hovered");
      }
    },

    isStartBuddy: function() {
      return (!this.getStartBuddy() && this.getBuddyArea().length > 0);
    },

    _onDragOver: function(ev) {
      var source = ev.getRelatedTarget();
      var colspan = source.getLayoutProperties().colSpan||1;
      var endCol = colspan + this.getLayoutProperties().column;
      if (colspan > 1) {
        // check + mark area if there is enough space
        if (!this.getStartBuddy()) {
          var area = this.getFreeArea(colspan);
          if (area.length < colspan) {
            // free area not big enough
            ev.preventDefault();
            this.resetHovered();
            gosa.ui.core.GridCellDropbox.setStartBuddy(null);
          } else {
            var start = area.shift();
            this.__setNewStartBuddy(start, area);
          }
        } else {
          // check if current start buddy is still relevant
          var area = this.getFreeArea(colspan);
          var start = area.shift();
          if (start !== this.getStartBuddy()) {
            // new start Buddy
            // clear the old one
            var oldStart = this.getStartBuddy();
            oldStart.setHovered(false);
            oldStart.getBuddyArea().removeAll();
            this.__setNewStartBuddy(start, area);
          } else {
            start.setHovered(true);
          }
        }
      } else if (endCol > this.__gridLayout.getColumnCount()) {
        ev.preventDefault();
      } else {
        this.setHovered(true);
      }
    },

    __setNewStartBuddy: function(start, area) {
      gosa.ui.core.GridCellDropbox.setStartBuddy(start);
      start.setBuddyArea(area);
      area.forEach(function(areaWidget) {
        areaWidget.setStartBuddy(start);
      }, this);
      start.setHovered(true);
    },

    getFreeArea: function(colspan) {
      var area = new qx.data.Array();
      var col, l;
      if (colspan == 1) {
        area.push(this);
      } else {
        var props = this.getLayoutProperties();
        var endCol = colspan + props.column;
        area.push(this);
        // get the last free cell in this row
        for (col=props.column+1, l=Math.min(this.__gridLayout.getColumnCount(), endCol); col < l; col++) {
          var widget = this.__gridLayout.getCellWidget(props.row, col);
          if (!(widget instanceof gosa.ui.core.GridCellDropbox)) {
            break;
          } else {
            area.push(widget);
          }
        }
        if (area.length < colspan) {
          // check cells before
          for (col=props.column-1, l=col-Math.max(0, colspan - area.length); col > l; col--) {
            var widget = this.__gridLayout.getCellWidget(props.row, col);
            if (!(widget instanceof gosa.ui.core.GridCellDropbox)) {
              break;
            } else {
              area.unshift(widget);
            }
          }
        }
      }
      return area
    },

    _onDragLeave: function() {
      if (!this.getStartBuddy() && !this.isStartBuddy()) {
        this.setHovered(false);
      }
    },

    _onDrop: function(ev) {
      if (this.getStartBuddy()) {
        var buddy = this.getStartBuddy();
        buddy.resetHovered();
        qx.event.message.Bus.dispatchByName("gosa.dashboard.drop", {
          widget : ev.getRelatedTarget(),
          props  : buddy.getLayoutProperties()
        });
      } else {
        this.resetHovered();
        qx.event.message.Bus.dispatchByName("gosa.dashboard.drop", {
          widget : ev.getRelatedTarget(),
          props  : this.getLayoutProperties()
        });
      }
      gosa.ui.core.GridCellDropbox.setStartBuddy(null);
    }
  },

  /*
  *****************************************************************************
     DESTRUCTOR
  *****************************************************************************
  */
  destruct : function() {
    this.__gridLayout = null;
  }
});