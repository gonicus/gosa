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
qx.Mixin.define("gosa.ui.tree.MMove", {

  /*
  *****************************************************************************
     MEMBERS
  *****************************************************************************
  */
  members : {

    onDrop: function(ev) {
      if (ev.supportsType(this.getDragDropType())) {
        var item = ev.getData(this.getDragDropType());
        if (item === this) {
          // cannot drop on itself
          return;
        }
        if (item instanceof gosa.ui.tree.Folder) {

          switch (this.getDecorator()) {
            case "drop-after":
              this.getParent().addAfter(item, this);
              break;

            default:
              this.getParent().addBefore(item, this);
              break;
          }
        } else {
          this.add(item);
        }
      }
    },

    onDragOver: function(e) {
      if (!e.supportsType(this.getDragDropType()) || this === e.getDragTarget()) {
        e.preventDefault();
      } else if (e.getDragTarget() instanceof gosa.ui.tree.Folder && this.getParent().getParent() !== null) {
        // folders only on root level
        console.log(this.getParent().getParent());
        e.preventDefault();
      } else {
        this.addListener("pointermove", this._onDragMove, this);
        this._onDragMove(e);
      }
    },

    _onDragLeave: function() {
      this.resetDecorator();
      this.removeListener("pointermove", this._onDragMove, this);
    },

    _onDragMove: function(e) {
      var bounds = this.getContentElement().getDomElement().getBoundingClientRect();
      var middle = bounds.top + (bounds.bottom - bounds.top)/2;
      if (e.getDocumentTop() >= middle) {
        this.setDecorator("drop-after");
      } else {
        this.setDecorator("drop-before");
      }
    }
  }
});
