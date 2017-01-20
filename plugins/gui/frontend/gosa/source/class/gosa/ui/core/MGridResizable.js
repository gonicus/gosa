/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org
  
   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de
  
   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html
  
   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

/**
 * Provides resizing behavior to any widget in a grid layout.
 */
qx.Mixin.define("gosa.ui.core.MGridResizable",
{
  /*
   *****************************************************************************
   CONSTRUCTOR
   *****************************************************************************
   */

  construct : function()
  {
    // Register listeners to the content
    var content = this.getContentElement();
    content.addListener("pointerdown", this.__onResizePointerDown, this, true);
    content.addListener("pointerup", this.__onResizePointerUp, this);
    content.addListener("pointermove", this.__onResizePointerMove, this);
    content.addListener("pointerout", this.__onResizePointerOut, this);
    content.addListener("losecapture", this.__onResizeLoseCapture, this);

    // Get a reference of the drag and drop handler
    var domElement = content.getDomElement();
    if (domElement == null) {
      domElement = window;
    }

    this.__dragDropHandler = qx.event.Registration.getManager(domElement).getHandler(qx.event.handler.DragDrop);
  },



  /*
   *****************************************************************************
   EVENTS
   *****************************************************************************
   */
  events : {
    "layoutChanged": "qx.event.type.Data"
  },


  /*
   *****************************************************************************
   PROPERTIES
   *****************************************************************************
   */

  properties :
  {
    /** Whether the top edge is resizable */
    resizableTop :
    {
      check : "Boolean",
      init : true
    },

    /** Whether the right edge is resizable */
    resizableRight :
    {
      check : "Boolean",
      init : true
    },

    /** Whether the bottom edge is resizable */
    resizableBottom :
    {
      check : "Boolean",
      init : true
    },

    /** Whether the left edge is resizable */
    resizableLeft :
    {
      check : "Boolean",
      init : true
    },

    /**
     * Property group to configure the resize behaviour for all edges at once
     */
    resizable :
    {
      group : [ "resizableTop", "resizableRight", "resizableBottom", "resizableLeft" ],
      mode  : "shorthand"
    },

    /** The tolerance to activate resizing */
    resizeSensitivity :
    {
      check : "Integer",
      init : 5
    },

    /** Whether a frame replacement should be used during the resize sequence */
    useResizeFrame :
    {
      check : "Boolean",
      init : true
    }
  },





  /*
   *****************************************************************************
   MEMBERS
   *****************************************************************************
   */

  members :
  {
    __dragDropHandler : null,
    __resizeFrame : null,
    __resizeActive : null,
    __resizeLeft : null,
    __resizeTop : null,
    __resizeStart : null,
    __resizeRange : null,


    RESIZE_TOP : 1,
    RESIZE_BOTTOM : 2,
    RESIZE_LEFT : 4,
    RESIZE_RIGHT : 8,


    /*
     ---------------------------------------------------------------------------
     CORE FEATURES
     ---------------------------------------------------------------------------
     */

    /**
     * Get the widget, which draws the resize/move frame. The resize frame is
     * shared by all widgets and is added to the root widget.
     *
     * @return {qx.ui.core.Widget} The resize frame
     */
    _getResizeFrame : function()
    {
      var frame = this.__resizeFrame;
      if (!frame)
      {
        frame = this.__resizeFrame = new qx.ui.core.Widget();
        frame.setAppearance("resize-frame");
        frame.exclude();

        qx.core.Init.getApplication().getRoot().add(frame);
      }

      return frame;
    },


    /**
     * Creates, shows and syncs the frame with the widget.
     */
    __showResizeFrame : function()
    {
      var location = this.getContentLocation();
      var frame = this._getResizeFrame();
      frame.setUserBounds(
      location.left,
      location.top,
      location.right - location.left,
      location.bottom - location.top
      );
      frame.show();
      frame.setZIndex(this.getZIndex()+1);
    },




    /*
     ---------------------------------------------------------------------------
     RESIZE SUPPORT
     ---------------------------------------------------------------------------
     */

    /**
     * Computes the new boundaries at each interval
     * of the resize sequence.
     *
     * @param e {qx.event.type.Pointer} Last pointer event
     * @return {Map} A map with the computed boundaries
     */
    __computeResizeResult : function(e)
    {
      // Detect mode
      var resizeActive = this.__resizeActive;

      // Read size hint
      var hint = this.getSizeHint();
      var range = this.__resizeRange;

      // Read original values
      var start = this.__resizeStart;
      var width = start.width;
      var height = start.height;
      var left = start.left;
      var top = start.top;
      var props = qx.lang.Object.clone(start.layoutProperties);
      var diff;
      var colDiff = 0;
      var rowDiff = 0;
      var removeWidgets = [];
      var layout, blocked, r, l, c, widget;

      if (
      (resizeActive & this.RESIZE_TOP) ||
      (resizeActive & this.RESIZE_BOTTOM)
      )
      {
        diff = Math.max(range.top, Math.min(range.bottom, e.getDocumentTop())) - this.__resizeTop;
        rowDiff = Math.round(diff/start.rowHeight);

        // check if new rowspan does not overlap existing widgets
        if (rowDiff > 0) {
          layout = this.getLayoutParent().getLayout();
          var startRow = props.row+props.rowSpan;
          blocked = false;
          for (r=0; r < rowDiff; r++) {
            for (c=0, l = props.colSpan||1; c < l; c++) {
              widget = layout.getCellWidget(r + startRow, c + props.column);
              if (widget) {
                if (!(widget instanceof gosa.ui.core.GridCellDropbox)) {
                  // existing widget -> do not resize
                  rowDiff = r - 1;
                  blocked = true;
                  break;
                }
                else {
                  removeWidgets.push(widget);
                }
              }
            }
            if (blocked) {
              break;
            }
          }
        }

        // snap to row
        diff = rowDiff * (start.rowHeight + this.__resizeRange.spacingY);

        if (resizeActive & this.RESIZE_TOP) {
          height -= diff;
        } else {
          height += diff;
        }

        if (height < hint.minHeight) {
          height = hint.minHeight;
        } else if (height > hint.maxHeight) {
          height = hint.maxHeight;
        }

        if (rowDiff) {
          if (resizeActive & this.RESIZE_TOP) {
            top += start.height - height;
            props.row += rowDiff;
            props.rowSpan = Math.max(1, props.rowSpan - rowDiff);
          }
          else {
            props.rowSpan = props.rowSpan + rowDiff;
          }
        }
      }

      if (
      (resizeActive & this.RESIZE_LEFT) ||
      (resizeActive & this.RESIZE_RIGHT)
      )
      {
        diff = Math.max(range.left, Math.min(range.right, e.getDocumentLeft())) - this.__resizeLeft;
        colDiff = Math.round(diff/start.columnWidth);

        if (resizeActive & this.RESIZE_RIGHT) {
          // check if new colspan does not overlap existing widgets
          if (colDiff > 0) {
            layout = this.getLayoutParent().getLayout();
            var startCol = props.column+props.colSpan;
            blocked = false;
            for (c=0; c < colDiff; c++) {
              for (r=0, l = props.rowSpan||1; r < l; r++) {
                widget = layout.getCellWidget(r + props.row, c + startCol);
                if (widget) {
                  if (!(widget instanceof gosa.ui.core.GridCellDropbox)) {
                    // existing widget -> do not resize
                    colDiff = c - 1;
                    blocked = true;
                    break;
                  }
                  else {
                    removeWidgets.push(widget);
                  }
                }
              }
              if (blocked) {
                break;
              }
            }
          }
        }

        // snap to column
        diff = colDiff * (start.columnWidth + this.__resizeRange.spacingX);

        if (resizeActive & this.RESIZE_LEFT) {
          width -= diff;
        } else {
          width += diff;
        }

        if (width < hint.minWidth) {
          width = hint.minWidth;
        } else if (width > hint.maxWidth) {
          width = hint.maxWidth;
        }

        if (colDiff) {
          if (resizeActive & this.RESIZE_LEFT) {
            left += start.width - width;
            props.column += colDiff;
            props.colSpan = Math.min(this.__resizeRange.columns, props.colSpan - colDiff);
          }
          else {
            props.colSpan = Math.min(this.__resizeRange.columns, props.colSpan + colDiff);
          }
        }
      }

      // props.rowSpan = Math.min(this.__resizeRange.rows, Math.ceil(height/start.rowHeight));

      return {
        // left and top of the visible widget
        viewportLeft : left,
        viewportTop : top,

        parentLeft : start.bounds.left + left - start.left,
        parentTop : start.bounds.top + top - start.top,

        // dimensions of the visible widget
        width : width,
        height : height,
        layoutProperties: props,
        removeWidgets: removeWidgets
      };
    },


    /**
     * @type {Map} Maps internal states to cursor symbols to use
     *
     * @lint ignoreReferenceField(__resizeCursors)
     */
    __resizeCursors :
    {
      1  : "n-resize",
      2  : "s-resize",
      4  : "w-resize",
      8  : "e-resize",

      5  : "nw-resize",
      6  : "sw-resize",
      9  : "ne-resize",
      10 : "se-resize"
    },


    /**
     * Updates the internally stored resize mode
     *
     * @param e {qx.event.type.Pointer} Last pointer event
     */
    __computeResizeMode : function(e)
    {
      var location = this.getContentLocation();
      var pointerTolerance = this.getResizeSensitivity();

      var pointerLeft = e.getDocumentLeft();
      var pointerTop = e.getDocumentTop();

      var resizeActive = this.__computeResizeActive(
      location, pointerLeft, pointerTop, pointerTolerance
      );

      // check again in case we have a corner [BUG #1200]
      if (resizeActive > 0) {
        // this is really a | (or)!
        resizeActive = resizeActive | this.__computeResizeActive(
        location, pointerLeft, pointerTop, pointerTolerance * 2
        );
      }

      this.__resizeActive = resizeActive;
    },


    /**
     * Internal helper for computing the proper resize action based on the
     * given parameters.
     *
     * @param location {Map} The current location of the widget.
     * @param pointerLeft {Integer} The left position of the pointer.
     * @param pointerTop {Integer} The top position of the pointer.
     * @param pointerTolerance {Integer} The desired distance to the edge.
     * @return {Integer} The resize active number.
     */
    __computeResizeActive : function(location, pointerLeft, pointerTop, pointerTolerance) {
      var resizeActive = 0;

      // TOP
      if (
      this.getResizableTop() &&
      Math.abs(location.top - pointerTop) < pointerTolerance &&
      pointerLeft > location.left - pointerTolerance &&
      pointerLeft < location.right + pointerTolerance
      ) {
        resizeActive += this.RESIZE_TOP;

        // BOTTOM
      } else if (
      this.getResizableBottom() &&
      Math.abs(location.bottom - pointerTop) < pointerTolerance &&
      pointerLeft > location.left - pointerTolerance &&
      pointerLeft < location.right + pointerTolerance
      ) {
        resizeActive += this.RESIZE_BOTTOM;
      }

      // LEFT
      if (
      this.getResizableLeft() &&
      Math.abs(location.left - pointerLeft) < pointerTolerance &&
      pointerTop > location.top - pointerTolerance &&
      pointerTop < location.bottom + pointerTolerance
      ) {
        resizeActive += this.RESIZE_LEFT;

        // RIGHT
      } else if (
      this.getResizableRight() &&
      Math.abs(location.right - pointerLeft) < pointerTolerance &&
      pointerTop > location.top - pointerTolerance &&
      pointerTop < location.bottom + pointerTolerance
      ) {
        resizeActive += this.RESIZE_RIGHT;
      }
      return resizeActive;
    },


    /*
     ---------------------------------------------------------------------------
     RESIZE EVENT HANDLERS
     ---------------------------------------------------------------------------
     */

    /**
     * Event handler for the pointer down event
     *
     * @param e {qx.event.type.Pointer} The pointer event instance
     */
    __onResizePointerDown : function(e)
    {
      // Check for active resize
      if (!this.__resizeActive || !this.getEnabled() || e.getPointerType() == "touch") {
        return;
      }

      // Add resize state
      this.addState("resize");

      // Store pointer coordinates
      this.__resizeLeft = e.getDocumentLeft();
      this.__resizeTop = e.getDocumentTop();

      // Compute range
      var parent = this.getLayoutParent();
      var parentLocation = parent.getContentLocation();
      var parentBounds = parent.getBounds();
      var parentLayout = parent.getLayout();

      this.__resizeRange = {
        left : parentLocation.left,
        top : parentLocation.top,
        right : parentLocation.left + parentBounds.width,
        bottom : parentLocation.top + parentBounds.height,
        columns: parentLayout.getColumnCount(),
        rows: parentLayout.getRowCount(),
        spacingX: parentLayout.getSpacingX(),
        spacingY: parentLayout.getSpacingY()
      };

      // Cache bounds
      var location = this.getContentLocation();
      var bounds   = this.getBounds();
      var layoutProperties = this.getLayoutProperties();
      var colspan = layoutProperties.colSpan || 1;
      var rowspan = layoutProperties.rowSpan || 1;
      var columnWidth = Math.floor((bounds.width - (colspan-1) * this.__resizeRange.spacingX) / colspan);
      var rowHeight = Math.floor((bounds.height - (rowspan-1) * this.__resizeRange.spacingY)/ rowspan);

      this.__resizeStart = {
        top : location.top,
        left : location.left,
        width : location.right - location.left,
        height : location.bottom - location.top,
        bounds : qx.lang.Object.clone(bounds),
        columnWidth : columnWidth,
        rowHeight : rowHeight,
        layoutProperties: qx.lang.Object.clone(layoutProperties)
      };

      // Show frame if configured this way
      if (this.getUseResizeFrame()) {
        this.__showResizeFrame();
      }

      // Enable capturing
      this.capture();

      // Stop event
      e.stop();
    },


    /**
     * Event handler for the pointer up event
     *
     * @param e {qx.event.type.Pointer} The pointer event instance
     */
    __onResizePointerUp : function(e)
    {
      // Check for active resize
      if (!this.hasState("resize") || !this.getEnabled() || e.getPointerType() == "touch") {
        return;
      }

      // Hide frame afterwards
      if (this.getUseResizeFrame()) {
        this._getResizeFrame().exclude();
      }

      // Compute bounds
      var bounds = this.__computeResizeResult(e);
      var startProps = this.__resizeStart.layoutProperties;
      var endProps = bounds.layoutProperties;

      bounds.removeWidgets.forEach(function(widget) {
        widget.destroy();
      }, this);

      // Sync with widget
      this.setLayoutProperties(endProps);

      // Clear mode
      this.__resizeActive = 0;

      // Remove resize state
      this.removeState("resize");

      // Reset cursor
      this.resetCursor();
      this.getApplicationRoot().resetGlobalCursor();

      // Disable capturing
      this.releaseCapture();

      e.stopPropagation();

      if (startProps.colSpan !== endProps.colSpan || startProps.rowSpan !== endProps.rowSpan) {
        // layout has changed
        this.fireDataEvent("layoutChanged", true);
      }
    },


    /**
     * Event listener for <code>losecapture</code> event.
     *
     * @param e {qx.event.type.Event} Lose capture event
     */
    __onResizeLoseCapture : function(e)
    {
      // Check for active resize
      if (!this.__resizeActive) {
        return;
      }

      // Reset cursor
      this.resetCursor();
      this.getApplicationRoot().resetGlobalCursor();

      // Remove drag state
      this.removeState("move");

      // Hide frame afterwards
      if (this.getUseResizeFrame()) {
        this._getResizeFrame().exclude();
      }
    },


    /**
     * Event handler for the pointer move event
     *
     * @param e {qx.event.type.Pointer} The pointer event instance
     */
    __onResizePointerMove : function(e)
    {
      if (!this.getEnabled() || e.getPointerType() == "touch") {
        return;
      }

      if (this.hasState("resize"))
      {
        var bounds = this.__computeResizeResult(e);

        // Update widget
        if (this.getUseResizeFrame())
        {
          // Sync new bounds to frame
          var frame = this._getResizeFrame();
          frame.setUserBounds(bounds.viewportLeft, bounds.viewportTop, bounds.width, bounds.height);
        }
        else
        {
          // Update size
          this.setLayoutProperties(bounds.layoutProperties);
        }

        // Full stop for event
        e.stopPropagation();
      }
      else if (!this.hasState("maximized") && !this.__dragDropHandler.isSessionActive())
      {
        this.__computeResizeMode(e);

        var resizeActive = this.__resizeActive;
        var root = this.getApplicationRoot();

        if (resizeActive)
        {
          var cursor = this.__resizeCursors[resizeActive];
          this.setCursor(cursor);
          root.setGlobalCursor(cursor);
        }
        else if (this.getCursor())
        {
          this.resetCursor();
          root.resetGlobalCursor();
        }
      }
    },


    /**
     * Event handler for the pointer out event
     *
     * @param e {qx.event.type.Pointer} The pointer event instance
     */
    __onResizePointerOut : function(e)
    {
      if (e.getPointerType() == "touch") {
        return;
      }
      // When the pointer left the window and resizing is not yet
      // active we must be sure to (especially) reset the global
      // cursor.
      if (this.getCursor() && !this.hasState("resize"))
      {
        this.resetCursor();
        this.getApplicationRoot().resetGlobalCursor();
      }
    }
  },

  /*
   *****************************************************************************
   DESTRUCTOR
   *****************************************************************************
   */

  destruct : function()
  {
    if(this.getCursor()) {
      this.getApplicationRoot().resetGlobalCursor();
    }

    if (this.__resizeFrame != null && !qx.core.ObjectRegistry.inShutDown)
    {
      this.__resizeFrame.destroy();
      this.__resizeFrame = null;
    }

    this.__dragDropHandler = null;
  }
});
