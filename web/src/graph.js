

function toJSON(res) { return res.json(); };

function printMe() {
    console.log('I get called from print.js!');
  }

function cytoscape(container, data, style) {
    container.innerHTML = _.join(['in', 'cytoscape'], ' ');
    return container;
    /*
    var cy = cytoscape({
        container: container,
        elements: data,
        style: style,
        layout: {
            name: 'grid',
            rows: 1
        }
    });
    */
};

export {cytoscape, toJSON, printMe};
