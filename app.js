document.addEventListener('DOMContentLoaded', () => {
    const selector = document.getElementById('play-selector');

    // Fetch corpus summary
    fetch('/api/corpus')
        .then(res => res.json())
        .then(data => {
            selector.innerHTML = '<option value="">Select a play...</option>';
            // Sort plays by title
            data.sort((a, b) => a.title.localeCompare(b.title));
            data.forEach(play => {
                const opt = document.createElement('option');
                opt.value = play.id;
                opt.textContent = `${play.author}: ${play.title}`;
                selector.appendChild(opt);
            });
        });

    selector.addEventListener('change', (e) => {
        const playId = e.target.value;
        if (!playId) return;

        fetch(`/api/play/${playId}`)
            .then(res => res.json())
            .then(data => {
                updateDashboard(data);
            });
    });
});

function updateDashboard(play) {
    // Update metadata
    document.getElementById('meta-author').textContent = play.author;
    document.getElementById('meta-title').textContent = play.title;

    // Update metrics
    document.getElementById('val-nodes').textContent = play.metrics.nodes;
    document.getElementById('val-edges').textContent = play.metrics.edges;
    document.getElementById('val-density').textContent = play.metrics.density.toFixed(3);
    document.getElementById('val-clustering').textContent = play.metrics.clustering.toFixed(3);

    renderNetwork(play.network);
    renderCentrality(play.network.nodes);
}

function renderNetwork(network) {
    // Simple Force-Directed layout using Plotly's scatter3d or scatter
    // Since Plotly doesn't have a built-in auto-layout for graphs in scatter,
    // we'll use a simple circular layout for demonstration.

    const nodes = network.nodes;
    const edges = network.edges;
    const n = nodes.length;

    const x = [];
    const y = [];
    const labels = [];
    const nodeIds = {};

    nodes.forEach((node, i) => {
        const angle = (2 * Math.PI * i) / n;
        x.push(Math.cos(angle));
        y.push(Math.sin(angle));
        labels.push(node.name);
        nodeIds[node.id] = i;
    });

    const edge_x = [];
    const edge_y = [];

    edges.forEach(edge => {
        const u = nodeIds[edge.source];
        const v = nodeIds[edge.target];
        if (u !== undefined && v !== undefined) {
            edge_x.push(x[u], x[v], null);
            edge_y.push(y[u], y[v], null);
        }
    });

    const edgeTrace = {
        x: edge_x,
        y: edge_y,
        line: { width: 1, color: '#888' },
        hoverinfo: 'none',
        mode: 'lines',
        type: 'scatter'
    };

    const nodeTrace = {
        x: x,
        y: y,
        mode: 'markers+text',
        text: labels,
        textposition: 'top center',
        hoverinfo: 'text',
        marker: {
            size: 15,
            color: '#0d6efd',
            line: { width: 2, color: 'white' }
        },
        type: 'scatter'
    };

    const layout = {
        showlegend: false,
        hovermode: 'closest',
        margin: { b: 20, l: 5, r: 5, t: 40 },
        xaxis: { showgrid: false, zeroline: false, showticklabels: false },
        yaxis: { showgrid: false, zeroline: false, showticklabels: false },
        plot_bgcolor: '#fff'
    };

    Plotly.newPlot('network-graph', [edgeTrace, nodeTrace], layout);
}

function renderCentrality(nodes) {
    // Sort nodes by degree
    const sortedNodes = [...nodes].sort((a, b) => b.degree - a.degree);

    const names = sortedNodes.map(n => n.name);
    const degrees = sortedNodes.map(n => n.degree);

    const trace = {
        x: names,
        y: degrees,
        type: 'bar',
        marker: { color: '#0d6efd' }
    };

    const layout = {
        title: 'Degree Centrality by Character',
        yaxis: { title: 'Centrality' },
        margin: { b: 100 }
    };

    Plotly.newPlot('centrality-chart', [trace], layout);
}
