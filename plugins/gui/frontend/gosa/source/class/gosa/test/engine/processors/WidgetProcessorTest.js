qx.Class.define("gosa.test.engine.processors.WidgetProcessorTest",
{
  extend : qx.dev.unit.TestCase,

  members :
  {
    __processor : null,

    setUp : function() {
      this.__processor = new gosa.engine.processors.WidgetProcessor();
    },

    tearDown : function() {
      this.__processor.dispose();
      this.__processor = null;
    },

    testWidgetCreation : function() {
      var container = new qx.ui.container.Composite(new qx.ui.layout.VBox());

      // simple label
      var json = {
        "class" : "qx.ui.basic.Label",
        "properties" : {
          backgroundColor : "red"
        }
      };
      this.__processor.process(json, container);
      this.assertEquals(1, container.getChildren().length);
      this.assertInstance(container.getChildren()[0], qx.ui.basic.Label);
      this.assertEquals("red", container.getChildren()[0].getBackgroundColor());

      // included form
      container.removeAll().forEach(function(widget) {
        widget.dispose();
      });

      var formProcessor = new gosa.engine.processors.FormProcessor();
      var formJson = {
        type : "form",
        symbol : "testWidgetForm",
        renderer : "qx.ui.form.renderer.Single"
      };
      formProcessor.process(formJson);
      formProcessor.dispose();
      formProcessor = null;

      json = {
        "form": "@testWidgetFormWidget"
      };
      this.__processor.process(json, container);

      this.assertEquals(1, container.getChildren().length);
      this.assertInstance(container.getChildren()[0], qx.ui.groupbox.GroupBox);

      var child = container.getChildren()[0];
      this.assertEquals(2, child.getChildren().length);
      this.assertInstance(child.getChildren()[0], qx.ui.form.renderer.Single);
      this.assertInstance(child.getChildren()[1], qx.ui.container.Composite);

      // nested
      container.removeAll().forEach(function(widget) {
        widget.dispose();
      });

      json = {
        "class" : "qx.ui.container.Composite",
        "layout" : "qx.ui.layout.HBox",
        "layoutConfig" : {
          alignY : "middle"
        },
        "children" : [
          {
            "class" : "qx.ui.container.Composite",
            "layout" : "qx.ui.layout.Atom",
            "children" : [
              {
                "class" : "qx.ui.basic.Label"
              }
            ]
          },
          {
            "class" : "qx.ui.form.TextField"
          }
        ]
      };
      this.__processor.process(json, container);

      this.assertEquals(1, container.getChildren().length);

      var firstLevel = container.getChildren()[0];
      this.assertEquals(2, firstLevel.getChildren().length);
      this.assertInstance(firstLevel, qx.ui.container.Composite);
      var layout = firstLevel.getLayout();
      this.assertInstance(layout, qx.ui.layout.HBox);
      this.assertEquals("middle", layout.getAlignY());

      var textField = firstLevel.getChildren()[1];
      this.assertInstance(textField, qx.ui.form.TextField);

      var secondLevel = firstLevel.getChildren()[0];
      this.assertInstance(secondLevel, qx.ui.container.Composite);
      this.assertEquals(1, secondLevel.getChildren().length);
      this.assertInstance(secondLevel.getLayout(), qx.ui.layout.Atom);

      var label = secondLevel.getChildren()[0];
      this.assertInstance(label, qx.ui.basic.Label);

      container.dispose();
    }
  }
});
