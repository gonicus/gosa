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

    /**
     * Global start buddy
     */
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
      var rowspan = source.getLayoutProperties().rowSpan||1;
      var endCol = colspan + this.getLayoutProperties().column;
      if (colspan > 1 || rowspan > 1) {
        var area = this.getFreeArea(colspan, rowspan);
        if (!area) {
          // free area not big enough
          ev.preventDefault();
          this.resetHovered();
          gosa.ui.core.GridCellDropbox.setStartBuddy(null);
          return;
        }
        var start = area.shift();
        // check + mark area if there is enough space
        if (!this.getStartBuddy()) {
          this.__setNewStartBuddy(start, area);
        } else {
          // check if current start buddy is still relevant
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

    getFreeArea: function(colspan, rowspan) {
      var area = new qx.data.Array();
      var col, l, row, lr;
      if (colspan === 1 && rowspan === 1) {
        area.push(this);
        return area;
      } else {
        var props = this.getLayoutProperties();
        var grid = this.__gridLayout;
        var columns = grid.getColumnCount();

        var possibleArea = {
          startCol: Math.max(0, props.column - colspan),
          endCol: Math.min(columns, props.column + colspan),
          startRow: Math.max(0, props.row - rowspan),
          endRow: props.row + rowspan
        };

        var colPointer = columns < (props.column + colspan) ? columns - colspan : props.column;
        var rowPointer = props.row;

        var checkArea = function(rowStart, colStart) {
          var widgets = new qx.data.Array();
          // collect free cells
          for (row = rowStart, lr = possibleArea.endRow; row < lr; row++) {
            for (col = colStart, l = possibleArea.endCol; col < l; col++) {
              var widget = grid.getCellWidget(row, col);
              if (!(widget instanceof gosa.ui.core.GridCellDropbox)) {
                return {row: row, column: col};
              } else {
                widgets.push(widget);
              }
            }
          }
          return widgets;
        };

        var result = checkArea(rowPointer, colPointer);
        if (qx.lang.Type.isArray(result)) {
          return result;
        }
      }
      return false;
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