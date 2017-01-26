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
    __possibleStartBuddies: null,

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
    },

    /**
     * Calculates the possible start cells of free areas
     * @param source {gosa.plugins.AbstractDashboardWidget}
     * @return {Array} array with start cells of free areas encoded as 'row|column' strings
     */
    getPossibleStartBuddies: function(source) {
      if (!this.__possibleStartBuddies) {
        var grid = gosa.view.Dashboard.getInstance().getChildControl("board").getLayout();
        var sourceProps = source.getLayoutProperties();
        var colspan = sourceProps.colSpan || 1;
        var rowspan = sourceProps.rowSpan || 1;

        var startCells = [];

        var isEmptyCell = function(widget) {
          return (!widget || widget === source || widget instanceof gosa.ui.core.GridCellDropbox);
        };

        var isStartCell = function(cellWidget, row, col) {
          if (isEmptyCell(cellWidget)) {
            if (colspan === 1 && rowspan === 1) {
              return true;
            }
            else if ((col + colspan) > grid.getColumnCount()) {
              // no enough columns
              return false;
            }
            else {
              // check for free space
              for (var r = row, lr = row + rowspan; r < lr; r++) {
                for (var c = col, lc = col + colspan; c < lc; c++) {
                  var widget = grid.getCellWidget(r, c);
                  if (!isEmptyCell(widget)) {
                    return false;
                  }
                }
              }
            }
            return true;
          } else {
            return false;
          }
        }.bind(this);

        for (var row = 1, lr = grid.getRowCount(); row < lr; row++) {
          for (var col = 0, lc = grid.getColumnCount(); col < lc; col++) {
            var cellWidget = grid.getCellWidget(row, col);
            if (isStartCell(cellWidget, row, col)) {
              startCells.push(row + "|" + col);
            }
          }
        }
        console.log(startCells);
        this.__possibleStartBuddies = startCells;
      }
      return this.__possibleStartBuddies;
    },

    resetPossibleStartBuddies: function() {
      this.__possibleStartBuddies = null;
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
      var startBuddies = gosa.ui.core.GridCellDropbox.getPossibleStartBuddies(source);
      var sourceProps = source.getLayoutProperties();
      var colspan = sourceProps.colSpan||1;
      var rowspan = sourceProps.rowSpan||1;

      var myProps = this.getLayoutProperties();
      var endCol = colspan + myProps.column;
      if (colspan > 1 || rowspan > 1) {
        var area = this.getFreeArea(colspan, rowspan, startBuddies);
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
          this.debug("new start cell "+start.getLayoutProperties().row+"/"+start.getLayoutProperties().column);
          this.__setNewStartBuddy(start, area);
        } else {
          // check if current start buddy is still relevant
          if (start !== this.getStartBuddy()) {
            this.debug("replacing start cell old: "+this.getStartBuddy().getLayoutProperties().row+"/"+
                       this.getStartBuddy().getLayoutProperties().column+", new: "+start.getLayoutProperties().row+"/"+start.getLayoutProperties().column);
            // new start Buddy
            this.__setNewStartBuddy(start, area);
          } else {
            start.setHovered(true);
          }
        }
      } else if (endCol >= this.__gridLayout.getColumnCount()) {
        ev.preventDefault();
      } else {
        this.setHovered(true);
      }
    },

    __setNewStartBuddy: function(start, area) {
      // clear the old one
      var oldStart = this.getStartBuddy();
      if (oldStart) {
        oldStart.setHovered(false);
        oldStart.getBuddyArea().forEach(function(widget) {
          widget.resetStartBuddy();
        }, this);
        oldStart.getBuddyArea().removeAll();
      }

      gosa.ui.core.GridCellDropbox.setStartBuddy(start);
      start.setBuddyArea(area);
      area.forEach(function(areaWidget) {
        areaWidget.setStartBuddy(start);
      }, this);
      start.setHovered(true);
    },

    getFreeArea: function(colspan, rowspan, startBuddies) {

      var col, l, row, lr;
      if (colspan === 1 && rowspan === 1) {
        return new qx.data.Array(this);
      } else {
        var props = this.getLayoutProperties();
        var grid = this.__gridLayout;

        if (startBuddies.length === 0) {
          return false;
        }

        var getArea = function(sr, sc) {
          var area = new qx.data.Array();
          // this cell is a start cell for a free area
          for (row = sr, lr = row + rowspan; row < lr; row++) {
            for (col = sc, l = col + colspan; col < l; col++) {
              var widget = grid.getCellWidget(row, col);
              if (widget instanceof gosa.ui.core.GridCellDropbox) {
                area.push(widget);
              } else if (widget) {
                this.error("this cell ("+row+"/"+col+") should be free but is is not => start cell ("+sr+"/"+sc+") is invalid");
                return false;
              }
            }
          }
          return area;
        }.bind(this);

        if (startBuddies.indexOf(props.row+"|"+props.column) >= 0) {
          return getArea(props.row, props.column);
        } else {
          // find the next start cell
          var rowPointer = props.row;
          var colPointer = props.column;
          var endRow = Math.max(1, rowPointer - rowspan);
          var endCol = Math.max(0, colPointer - colspan);

          // console.log("RowPointer: %d, (>%d), ColPointer: %d (>%d)", rowPointer, endRow, colPointer, endCol);
          while (rowPointer >= endRow && colPointer >= endCol) {
            // console.log("checking on pointer row: %d, column: %d", rowPointer, colPointer);
            if (startBuddies.indexOf(rowPointer+"|"+colPointer) >= 0) {
              // console.log("1 found area starting from %d/%d", rowPointer, colPointer);
              return getArea(rowPointer, colPointer);
            } else {
              // go one row up and start from props.column to colPointer -1
              var currentRow = rowPointer;
              for (var cc = props.column; cc >= endCol; cc--) {
                // console.log("ROW check row: %d, column: %d", currentRow, cc);
                if (startBuddies.indexOf(currentRow + "|" + cc) >= 0) {
                  // console.log("2 found area starting from %d/%d", currentRow, cc);
                  return getArea(currentRow, cc);
                }
              }
              // nothing found, move the pointers
              rowPointer--;
            }
          }
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