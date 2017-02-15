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
* Extended Flow layout, that adds the property 'newLine' to allow widgets to start a new line
*/
qx.Class.define("gosa.ui.layout.Flow", {
  extend : qx.ui.layout.Flow,
    
  properties : {
    
  },
    
  members : {
    // overridden
    verifyLayoutProperty : qx.core.Environment.select("qx.debug",
    {
      "true" : function(item, name, value) {
        var validProperties = ["lineBreak", "stretch", "newLine"];
        this.assertInArray(name, validProperties, "The property '"+name+"' is not supported by the flow layout!" );
      },

      "false" : null
    }),

    /**
     * The FlowLayout tries to add as many Children as possible to the current 'Line'
     * and when it sees that the next Child won't fit, it starts on a new Line, continuing
     * until all the Children have been added.
     * To enable alignX "left", "center", "right" renderLayout has to calculate the positions
     * of all a Line's children before it draws them.
     *
     * @param availWidth {Integer} Final width available for the content (in pixel)
     * @param availHeight {Integer} Final height available for the content (in pixel)
     * @param padding {Map} Map containing the padding values. Keys:
     * <code>top</code>, <code>bottom</code>, <code>left</code>, <code>right</code>
     */
    renderLayout : function(availWidth, availHeight, padding)
    {
      var children = this._getLayoutChildren();

      if (this.getReversed()) {
        children = children.concat().reverse();
      }

      var lineCalculator = new qx.ui.layout.LineSizeIterator(
      children,
      this.getSpacingX()
      );

      var lineTop = padding.top;
      while (lineCalculator.hasMoreLines())
      {
        var line = lineCalculator.computeNextLine(availWidth);
        this.___renderLine(line, lineTop, availWidth, padding);
        lineTop += line.height + this.getSpacingY();
      }
    },

    /**
     * Render a line in the flow layout
     *
     * @param line {Map} A line configuration as returned by
     *    {@link LineSizeIterator#computeNextLine}.
     * @param lineTop {Integer} The line's top position
     * @param availWidth {Integer} The available line width
     * @param padding {Map} Map containing the padding values. Keys:
     * <code>top</code>, <code>bottom</code>, <code>left</code>, <code>right</code>
     */
    ___renderLine : function(line, lineTop, availWidth, padding)
    {
      var util = qx.ui.layout.Util;

      var left = padding.left;
      if (this.getAlignX() != "left") {
        left = padding.left + availWidth - line.width;
        if (this.getAlignX() == "center") {
          left = padding.left + Math.round((availWidth - line.width) / 2);
        }
      }

      for (var i=0; i<line.children.length; i++)
      {
        var child = line.children[i];
        var size = child.getSizeHint();
        var marginTop = child.getMarginTop();
        var marginBottom = child.getMarginBottom();

        var top = util.computeVerticalAlignOffset(
        child.getAlignY() || this.getAlignY(),
        marginTop + size.height + marginBottom,
        line.height,
        marginTop, marginBottom
        );

        var layoutProps = child.getLayoutProperties();
        if (layoutProps.stretch && layoutProps.stretch) {
          size.width += availWidth - line.width;
        }
        var nextLayoutProps = (i+1) < line.children.length ? line.children[i+1].getLayoutProperties() : {};
        if (nextLayoutProps.newLine && nextLayoutProps.newLine) {
          size.width += availWidth - line.width;
        }

        child.renderLayout(
        left + line.gapsBefore[i],
        lineTop + top,
        size.width,
        size.height
        );

        left += line.gapsBefore[i] + size.width;
      }
    }
  }
});