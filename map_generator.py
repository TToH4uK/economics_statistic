import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

DATA_PATH = "datasets/economic_data_1980_2020.csv"
OUTPUT_FILE = "interactive_economic_map.html"

def generate_map():
    if not os.path.exists(DATA_PATH):
        print(f"Ошибка: Файл {DATA_PATH} не найден.")
        return

    df = pd.read_csv(DATA_PATH).sort_values(by="Year")
    
    color_map = {
        "Hyperinflation": "darkviolet",
        "Overheating": "red",
        "Stagflation": "orange",
        "Healthy Growth": "green",
        "Steady Growth": "yellowgreen",
        "Recession": "peru",
        "Deflation": "blue",
        "Other": "gray",
        "Unknown": "#444"
    }
    ordered_conditions = list(color_map.keys())

    first_year = df['Year'].min()
    dummies = []
    for cond in ordered_conditions:
         dummies.append({
            "Year": first_year,
            "ISO_Code": "DUM", 
            "Country": "Initialization",
            "Economic_Condition": cond,
            "Real_GDP_Growth": 0,
            "GDP": 0,
            "Inflation": 0
        })
    df = pd.concat([df, pd.DataFrame(dummies)], ignore_index=True)

    fig_gdp = px.choropleth(
        df, locations="ISO_Code", locationmode="ISO-3",
        color="Real_GDP_Growth", animation_frame="Year",
        color_continuous_scale="RdYlGn", range_color=[-10, 10],
        hover_data={"Country": True, "GDP": ":,.0f", "Inflation": ":.2f", "Real_GDP_Growth": ":.2f"},
        template="plotly_dark"
    )
    
    fig_cond = px.choropleth(
        df, locations="ISO_Code", locationmode="ISO-3",
        color="Economic_Condition", animation_frame="Year",
        color_discrete_map=color_map,
        category_orders={"Economic_Condition": ordered_conditions},
        hover_data={"Country": True},
        template="plotly_dark"
    )
    
    fig_gdp.update_traces(showlegend=False)
    fig_cond.update_traces(showlegend=False)
    for frame in fig_gdp.frames:
        for t in frame.data: t.showlegend = False
    for frame in fig_cond.frames:
        for t in frame.data: t.showlegend = False

    traces_gdp = list(fig_gdp.data)
    traces_cond = list(fig_cond.data)
    
    final_fig = go.Figure(
        data=traces_gdp + traces_cond,
        layout=fig_gdp.layout
    )
    final_fig.frames = []
    
    frames = []
    for f1, f2 in zip(fig_gdp.frames, fig_cond.frames):
        frames.append(go.Frame(data=list(f1.data) + list(f2.data), name=f1.name))
    final_fig.frames = frames
    
    legend_html = "<b style='font-size:16px'>Conditions</b><br>"
    for state, color in color_map.items():
        legend_html += f'<span style="color:{color}; font-size:18px">●</span> {state}<br>'
        
    custom_legend = dict(
        text=legend_html,
        align='left',
        showarrow=False,
        xref='paper', yref='paper',
        x=1.02, y=0.5,
        xanchor='left', yanchor='middle',
        bgcolor='rgba(30,30,30,0.9)',
        bordercolor='#555',
        borderwidth=1,
        font=dict(size=14, color="#fff")
    )

    n_gdp, n_cond = len(traces_gdp), len(traces_cond)
    vis_gdp = [True]*n_gdp + [False]*n_cond
    final_fig.update_layout(
        template="plotly_dark",
        height=750,
        margin=dict(r=250, l=30, t=30, b=0), # Уменьшен верхний отступ, так как кнопки теперь внешние
        showlegend=False,
        annotations=[],
        paper_bgcolor='#1e1e1e',
        plot_bgcolor='#1e1e1e',
        geo=dict(
            projection_scale=1.1,
            center=dict(lat=20, lon=0),
            showframe=False,
            bgcolor='#1e1e1e',
            showland=True,
            landcolor='#3a3a3a',
            showcountries=True,
            countrycolor='#666',
            coastlinecolor='#666',
            lakecolor='#1e1e1e'
        )
    )

    key_years = {
        1991: "1991: USSR Collapse",
        1997: "1997: Asian Crisis",
        1998: "1998: Russian Default",
        2008: "2008: GFC",
        2009: "2009: Eurozone Crisis",
        2011: "2011: Arab Spring",
        2013: "2013: Ukraine Crisis",
        2014: "2014: Crimea annexation",
        2015: "2015: Migration Crisis",
        2016: "2016: Brexit",
        2020: "2020: COVID-19"
    }

    if final_fig.layout.sliders:
        for step in final_fig.layout.sliders[0].steps:
            try:
                year = int(step.label)
                if year in key_years:
                    step.label = key_years[year]
            except (ValueError, TypeError):
                continue

    history_df = df[df['ISO_Code'] != "DUM"][['ISO_Code', 'Country', 'Year', 'Real_GDP_Growth', 'Inflation']].sort_values(['ISO_Code', 'Year'])
    
    country_data = {}
    for iso in history_df['ISO_Code'].unique():
        country_df = history_df[history_df['ISO_Code'] == iso]
        country_data[iso] = {
            "name": country_df['Country'].iloc[0],
            "years": country_df['Year'].tolist(),
            "gdp": country_df['Real_GDP_Growth'].tolist(),
            "inflation": country_df['Inflation'].tolist()
        }
    
    import json
    json_data = json.dumps(country_data)
    json_custom_legend = json.dumps(custom_legend)

    map_html = final_fig.to_html(include_plotlyjs='cdn', full_html=False, div_id='main-map')
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>Economic Dashboard 1980-2020</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #121212; color: #e0e0e0; }}
            .container {{ display: flex; flex-direction: column; gap: 20px; max-width: 1600px; margin: auto; }}
            .card {{ background: #1e1e1e; padding: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); border: 1px solid #333; }}
            #map-container {{ height: 850px; overflow: hidden; }}
            #chart-container {{ min-height: 450px; }}
            h1 {{ margin-top: 0; color: #ffffff; text-align: center; font-weight: 300; letter-spacing: 1px; }}
            
            .controls-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 0 10px; }}
            .btn-group {{ display: flex; gap: 8px; align-items: center; }}
            .btn-label {{ font-size: 0.85em; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-right: 5px; }}
            .btn {{ 
                background: #252525; border: 1px solid #444; color: #aaa; padding: 6px 14px; 
                border-radius: 6px; cursor: pointer; font-size: 0.9em; transition: all 0.2s; 
            }}
            .btn:hover {{ background: #333; color: #fff; border-color: #666; }}
            .btn.active {{ background: #3498db; color: #fff; border-color: #3498db; box-shadow: 0 0 10px rgba(52, 152, 219, 0.4); }}
            
            .placeholder {{ display: flex; align-items: center; justify-content: center; height: 100%; color: #666; font-size: 1.2em; border: 2px dashed #333; border-radius: 8px; }}
            
            #selected-country-header {{ 
                display: none; 
                font-size: 1.6em; 
                font-weight: 300; 
                color: #3498db; 
                margin-bottom: 15px; 
                text-align: center;
                letter-spacing: 1px;
                text-transform: uppercase;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Global Economic Dynamics (1980 - 2020)</h1>
            <div class="card" style="padding-bottom: 10px;">
                <div class="controls-bar">
                    <div class="btn-group" id="view-controls">
                        <span class="btn-label">Layer:</span>
                        <button class="btn active" onclick="switchView('gdp', this)">GDP Growth</button>
                        <button class="btn" onclick="switchView('cond', this)">Economic Condition</button>
                    </div>
                    <div class="btn-group" id="projection-controls">
                        <span class="btn-label">View:</span>
                        <button class="btn active" onclick="switchProjection('flat', this)">Flat</button>
                        <button class="btn" onclick="switchProjection('globe', this)">Globe</button>
                    </div>
                </div>
                <div id="map-container">
                    {map_html}
                </div>
            </div>
            <div class="card" id="chart-container" style="min-height: 450px; position: relative;">
                <div id="chart-placeholder" class="placeholder">
                    Click on a country on the map to see its economic history
                </div>
                <div id="selected-country-header"></div>
                <div id="line-chart" style="height: 450px; width: 100%;"></div>
            </div>
        </div>

        <script>
            const countryHistory = {json_data};
            
            const mapDiv = document.getElementById('main-map');
            const chartPlaceholder = document.getElementById('chart-placeholder');
            const chartOutput = document.getElementById('line-chart');
            const lineChartDiv = document.getElementById('line-chart');
            const countryHeader = document.getElementById('selected-country-header');

            const n_gdp = {n_gdp};
            const n_cond = {n_cond};
            const vis_gdp = Array(n_gdp).fill(true).concat(Array(n_cond).fill(false));
            const vis_cond = Array(n_gdp).fill(false).concat(Array(n_cond).fill(true));
            const customLegend = {json_custom_legend};

            window.switchView = function(mode, btn) {{
                console.log('Switching view to:', mode);
                const isGDP = mode === 'gdp';
                const visibility = isGDP ? vis_gdp : vis_cond;
                const annotations = isGDP ? [] : [customLegend];
                
                Plotly.update(mapDiv, 
                    {{ visible: visibility }}, 
                    {{ annotations: annotations, 'coloraxis.showscale': isGDP }}
                );
                
                document.querySelectorAll('#view-controls .btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }};

            window.switchProjection = function(type, btn) {{
                console.log('Switching projection to:', type);
                const isGlobe = type === 'globe';
                    const update = isGlobe ? {{
                        'geo.projection.type': 'orthographic',
                        'geo.projection.scale': 1.0,
                        'geo.projection.rotation': {{ lat: 0, lon: 0, roll: 0 }},
                        'geo.center': {{ lat: 0, lon: 0 }},
                        'geo.fitbounds': false
                    }} : {{
                        'geo.projection.type': 'equirectangular',
                        'geo.projection.scale': 1.1,
                        'geo.projection.rotation': {{ lat: 0, lon: 0, roll: 0 }},
                        'geo.center': {{ lat: 20, lon: 0 }},
                        'geo.fitbounds': false
                    }};
                
                Plotly.relayout(mapDiv, update);
                
                document.querySelectorAll('#projection-controls .btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }};
            
            const checkReady = setInterval(() => {{
                if (window.Plotly && mapDiv && mapDiv.data) {{
                    clearInterval(checkReady);
                    Plotly.restyle(mapDiv, {{ visible: vis_gdp }});
                }}
            }}, 100);

            const checkPlotly = setInterval(() => {{
                if (window.Plotly && mapDiv && mapDiv.on) {{
                    console.log('Plotly is ready, attaching listener to #main-map');
                    clearInterval(checkPlotly);
                    
                    mapDiv.on('plotly_click', function(data) {{
                        console.log('Map click event triggered!', data);
                        if (!data.points || data.points.length === 0) {{
                            console.warn('No points in click data');
                            return;
                        }}
                        
                        const point = data.points[0];
                        const iso = point.location;
                        console.log('ISO Code detected from click:', iso);
                        
                        if (iso && countryHistory[iso]) {{
                            const name = countryHistory[iso].name;
                            console.log('Found history for country:', name);
                            
                            chartPlaceholder.style.display = 'none';
                            countryHeader.innerText = name;
                            countryHeader.style.display = 'block';
                            
                            setTimeout(() => {{
                                renderChart(countryHistory[iso]).then(() => {{
                                    window.scrollTo({{ top: document.body.scrollHeight, behavior: 'smooth' }});
                                }}).catch(err => {{
                                    console.error('Error during scroll or render sequence:', err);
                                }});
                            }}, 50);
                        }} else {{
                            console.warn('No data found for ISO code:', iso);
                        }}
                    }});
                }}
            }}, 500);

            async function renderChart(data) {{
                try {{
                    console.log('Starting renderChart for:', data.name);
                    const gdpTrace = {{
                        x: data.years,
                        y: data.gdp,
                        name: 'GDP Growth (%)',
                        type: 'scatter',
                        mode: 'lines+markers',
                        line: {{ color: '#27ae60', width: 3 }},
                        marker: {{ size: 6 }}
                    }};

                    const inflationTrace = {{
                        x: data.years,
                        y: data.inflation,
                        name: 'Inflation (%)',
                        yaxis: 'y2',
                        type: 'scatter',
                        mode: 'lines+markers',
                        line: {{ color: '#e74c3c', width: 3, dash: 'dot' }},
                        marker: {{ size: 6 }}
                    }};

                    const layout = {{
                        template: 'plotly_dark',
                        title: `<b>Economic History: ${{data.name}}</b>`,
                        font: {{ color: '#fff' }},
                        xaxis: {{ 
                            title: 'Year', 
                            gridcolor: '#444', 
                            zerolinecolor: '#555',
                            tickfont: {{ color: '#fff' }}
                        }},
                        yaxis: {{ 
                            title: 'GDP Growth (%)', 
                            titlefont: {{color: '#2ecc71', size: 14}}, 
                            tickfont: {{color: '#2ecc71'}}, 
                            gridcolor: '#444',
                            zerolinecolor: '#555'
                        }},
                        yaxis2: {{
                            title: 'Inflation (%)',
                            titlefont: {{color: '#e74c3c', size: 14}},
                            tickfont: {{color: '#e74c3c'}},
                            overlaying: 'y',
                            side: 'right',
                            gridcolor: '#444'
                        }},
                        hovermode: 'x unified',
                        hoverlabel: {{ bgcolor: '#222', font: {{color: '#fff', size: 14}} }},
                        margin: {{ l: 60, r: 60, t: 80, b: 60 }},
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        legend: {{ 
                            orientation: 'h', 
                            y: 1.1, 
                            font: {{size: 12, color: '#fff'}},
                            bgcolor: 'rgba(30,30,30,0.8)',
                            bordercolor: '#555',
                            borderwidth: 1
                        }}
                    }};

                    console.log('Calling Plotly.react...');
                    await Plotly.react('line-chart', [gdpTrace, inflationTrace], layout, {{responsive: true}});
                    console.log('Plotly.react completed successfully');
                }} catch (error) {{
                    console.error('CRITICAL ERROR in renderChart:', error);
                    alert('Error rendering chart. See console (F12) for details.');
                }}
            }}
        </script>
    </body>
    </html>
    """

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print(f"Готово! Дашборд создан в {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_map()