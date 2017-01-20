/*========================================================================

   This file is part of the GOsa project -  http://gosa-project.org

   Copyright:
      (C) 2010-2017 GONICUS GmbH, Germany, http://www.gonicus.de

   License:
      LGPL-2.1: http://www.gnu.org/licenses/lgpl-2.1.html

   See the LICENSE file in the project's top-level directory for details.

======================================================================== */

qx.Theme.define("gosa.theme.Font",
{
  extend : qx.theme.indigo.Font,

  fonts :
  {
    "underline" :
    {
      size : 12,
      color: "font",
      lineHeight: 1.8,
      decoration: "underline",
      family: ['Open Sans', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
      sources: [
        {
          family: "Open Sans",
          source: [
            "gosa/fonts/OpenSans-Regular.ttf"
          ]
        }
      ]
    },

    "SearchResultTitle" : {
      size : 13,
      lineHeight : 1.4,
      bold: true,
      color: "blue",
      decoration: "underline",
      family: ['Open Sans', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
      sources: [
        {
          family: "Open Sans",
          source: [
            "gosa/fonts/OpenSans-Bold.ttf"
          ]
        }
      ]
    },

    "Title": {
      size : 18,
      color: "font",
      bold: true,
      lineHeight: 1.8,
      family: ['Open Sans', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
      sources: [
        {
          family: "Open Sans",
          source: [
            "gosa/fonts/OpenSans-Bold.ttf"
          ]
        }
      ]
    },

    "Subtitle": {
      size : 14,
      color: "font",
      bold: true,
      lineHeight: 1.4,
      family: ['Open Sans', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
      sources: [
        {
          family: "Open Sans",
          source: [
            "gosa/fonts/OpenSans-Bold.ttf"
          ]
        }
      ]
    },

    "Ligature": {
      size: 40,
      lineHeight: 1,
      comparisonString : "\uf1e3\uf1f7\uf11b\uf19d",
      family: ["Ligature"],
      sources: [
        {
          family: "Ligature",
          source: [
            "gosa/fonts/LigatureSymbols-2.11.eot",
            "gosa/fonts/LigatureSymbols-2.11.woff",
            "gosa/fonts/LigatureSymbols-2.11.ttf"
          ]
        }
      ]
    },

    "Logo": {
      size: 32,
      lineHeight: 1,
      family: ["Abel"],
      sources: [
        {
          family: "Abel",
          source: [
            "gosa/fonts/Abel-Regular.ttf"
          ]
        }
      ]
    },

    // - FLAT - do not insert anything behind this marker -----------------------------------------------------

    "default": {
      size: 14,
      family: ['Open Sans', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
      sources: [
        {
          family: "Open Sans",
          source: [
            "gosa/fonts/OpenSans-Regular.ttf"
          ]
        }
      ]
    },

    "small" : {
      size: 12,
      family: ['Open Sans', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
      sources: [
        {
          family: "Open Sans",
          source: [
            "gosa/fonts/OpenSans-Regular.ttf"
          ]
        }
      ]
    },

    "bold" : {
      size: 14,
      bold: true,
      family: ['Open Sans', 'Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
      sources: [
        {
          family: "Open Sans",
          source: [
            "gosa/fonts/OpenSans-Bold.ttf"
          ]
        }
      ]
    }
  }
});
