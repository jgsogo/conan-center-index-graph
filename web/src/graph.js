import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
cytoscape.use(dagre);


function toJSON(res) { return res.json(); };

function printMe() {
    console.log('I get called from print.js!');
}

function get_graph(container, data, style) {
    //container.innerHTML = _.join(['in', 'cytoscape'], ' ');
    //return container;


    var cy = cytoscape({
        container: container,
        elements: data,
        style: style,
        layout: {
            name: 'dagre',  // https://github.com/cytoscape/cytoscape.js-dagre
            nodeDimensionsIncludeLabels: true,
            nodeSep: 100,
            rankSep: 200,
            //ranker: 'tight-tree',
        },
        ready: function () {
            //this.style().clear();
            this.nodes().forEach(function (ele) {
                console.log(ele.id())
                //rect = document.getElementById('node-' + ele.id()).getBoundingClientRect();
                /*ele.style({
                    'width': rect.width*8,
                    'height': rect.height*8,
                  })*/
            });
        }
    });

    return cy;

};

export { get_graph, toJSON, printMe };
