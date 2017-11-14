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
    __last: null,
    __currentSourceType: null,

    onDrop: function(ev) {
      if (ev.supportsType(this.getDragDropType())) {
        var item = ev.getData(this.getDragDropType());
        var target = this;
        if (item instanceof gosa.ui.tree.Folder) {
          while (target instanceof gosa.ui.tree.Application) {
            target = this.getParent();
          }
          var decorator = target.getDecorator() && target.getDecorator().startsWith("drop-") ? target.getDecorator() : target.getChildrenContainer().getDecorator();
          switch (decorator) {
            case "drop-before":
              target.getParent().addBefore(item, target);
              break;

            default:
              target.getParent().addAfter(item, target);
              break;
          }
          target.resetDecorator();
          target.getChildrenContainer().resetDecorator();
        } else {
          if (this instanceof gosa.ui.tree.Folder) {
            // just add
            this.add(item);
          } else {
            switch (this.getDecorator()) {
              case "drop-before":
                this.getParent().addBefore(item, this);
                break;

              default:
                this.getParent().addAfter(item, this);
                break;
            }
          }
        }
      }
      this.__resetDecorators();
    },

    _afterDragStart: function() {
      var tree = this.getTree();
      tree.addListener("pointermove", this._onDragMove, this);
      this.addListenerOnce("dragend", function() {
        tree.removeListener("pointermove", this._onDragMove, this);
        this.__currentSourceType = null;
      }, this);
      this.__currentSourceType = this instanceof gosa.ui.tree.Folder ? "folder" : "application";
    },

    __resetDecorators: function() {
      this.resetDecorator();
      this.getChildrenContainer().resetDecorator();
      if (this.__last) {
        this.__last.resetDecorator();
        this.__last.getChildrenContainer().resetDecorator();
        this.__last = null;
      }
    },

    onDragOver: function(e) {
      if (!e.supportsType(this.getDragDropType()) || this === e.getDragTarget()) {
        e.preventDefault();
      }
    },

    _onDragMove: function(e) {
      var current = e.getTarget();
      if (this.__currentSourceType === "application") {
        if (current instanceof gosa.ui.tree.Application) {
          // move before or after
          var bounds = current.getContentElement().getDomElement().getBoundingClientRect();
          var middle = bounds.top + (bounds.bottom - bounds.top) / 2;
          if (e.getDocumentTop() >= middle) {
            current.setDecorator("drop-after");
          } else {
            current.setDecorator("drop-before");
          }
        } else {
          current.resetDecorator();
        }
        if (this.__last && this.__last !== current) {
          this.__last.resetDecorator();
        }
        this.__last = current;
      } else {
        while (current instanceof gosa.ui.tree.Application) {
          current = current.getParent();
        }
        if (current instanceof gosa.ui.tree.Folder) {
          var bounds = current.getContentElement().getDomElement().getBoundingClientRect();
          var top = bounds.top;
          var bottom = bounds.bottom;
          var childContainer = current.getChildrenContainer().getContentElement().getDomElement();
          if (childContainer) {
            var childBounds = childContainer.getBoundingClientRect();
            if (childBounds.bottom) {
              bottom = childBounds.bottom;
            }
          }
          var middle = top + (bottom - top) / 2;
          if (e.getDocumentTop() >= middle) {
            if (childContainer) {
              current.getChildrenContainer().setDecorator("drop-after");
              current.resetDecorator();
            } else {
              current.setDecorator("drop-after");
            }
          } else {
            current.setDecorator("drop-before");
            if (childContainer) {
              current.getChildrenContainer().resetDecorator();
            }
          }
          if (this.__last && this.__last !== current) {
            this.__last.resetDecorator();
            this.__last.getChildrenContainer().resetDecorator();
          }
          this.__last = current;
        } else if (this.__last) {
          this.__last.resetDecorator();
          this.__last.getChildrenContainer().resetDecorator();
          this.__last = null;
        }
      }
    }
  }
});
