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

/**
* Mixin adds drag&drop support for widgets
*/
qx.Mixin.define("gosa.ui.widgets.MDragDrop", {

  /*
  *****************************************************************************
     PROPERTIES
  *****************************************************************************
  */
  properties : {

    dragDropType: {
      check: "String",
      init: "gosa/default"
    }
  },

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {
    _dragDropActions: null,

    _initDrapDropListeners: function() {
      // drag&drop
      if (this.isDraggable()) {
        this.addListener("dragstart", this._onDragStart, this);
        this.addListener("droprequest", this._onDropRequest, this);
      }
      if (this.isDroppable()) {
        this.addListener("dragover", this._onDragOver, this);
      }
    },

    _applyDragDropGuiProperties: function(props) {
      if('dragDropType' in props) {
        this.setDragDropType(props.dragDropType);
      }
      if('droppable' in props && props.droppable === true) {
        this.setDroppable(true);
        this.addListener("drop", this._onDrop, this);
      }
      if('draggable' in props && props.draggable === true) {
        this.setDraggable(true);
      }
      if('dragDropActions' in props) {
        this._dragDropActions = props.dragDropActions;
      } else {
        this._dragDropActions = ["move", "copy"];
      }
    },

    _onDragStart: function(e) {
      this._dragDropActions.forEach(e.addAction, e);

      e.addType(this.getDragDropType());
    },

    _onDrop: function(ev) {
      if (this.onDrop) {
        this.onDrop(ev);
      } else {
        if (ev.supportsType(this.getDragDropType())) {
          var items = ev.getData(this.getDragDropType());
          var values = this.getValue();
          items.forEach(function(entry) {
            if (!values.contains(entry)) {
              values.push(entry);
            }
          });
          if (items.length) {
            this.fireDataEvent("changeValue", values.copy());
          }
        }
      }
    },

    _onDragOver: function(e) {
      if (!e.supportsType(this.getDragDropType())) {
        e.preventDefault();
      }
    }
  }
});