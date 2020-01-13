/* global document, window, fetch, cytoscape */

(function () {
    var toJson = function (res) { return res.json(); };

    window.cy = cytoscape({
        container: document.getElementById('cy'),
        style: fetch('cy-style.json').then(toJson),
        elements: fetch('data.json').then(toJson),
        layout: {
            name: 'grid'
        },
        ready: function () {
            //this.style().clear();
            this.nodes().forEach(function(ele) {
                console.log(ele.id())
                rect = document.getElementById('node-' + ele.id()).getBoundingClientRect();
                ele.style({
                    'width': rect.width/2.,
                    'height': rect.height/2.,
                  })
              });
        }
    });

    window.cy.nodeHtmlLabel([
        {
            query: 'node[type="regular"]',
            tpl: function (data) {
                return `<table id="node-${data.id}" class="cy-node-table"><tr><td class="cy-node-title">${data.name}</td></tr><tr><td>${data.versions}</td></tr><tr><td>${data.profiles}</td></tr></table>`;
            }
        },
        {
            query: 'node[type="draft"]',
            tpl: function (data) {
                return `<table id="node-${data.id}" class="cy-node-table"><tr><td class="cy-node-title">${data.name}</td></tr><tr><td>${data.profiles}</td></tr></table>`;
            }
        }
    ]);
})();
