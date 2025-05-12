import json

import requests
import streamlit as st
import streamlit.components.v1 as components
from bs4 import BeautifulSoup

st.set_page_config("Baller", ":basketball:", layout="wide")
st.title(":basketball: Baller")


@st.cache_data(ttl=300)
def fetch(url: str):
    r = requests.get(url)
    r.raise_for_status()
    return r.text


soup = BeautifulSoup(
    fetch(
        "https://www.ballertv.com/teams/drive-richmond-u11-elite-2-red-wpgdnbyjzdss1s9ivgiu"
    ),
    features="html.parser",
)

team_info = json.loads(
    soup.select_one('div[data-react-props][data-react-class="profiles/teams/Show"]')[
        "data-react-props"
    ]
)

team_name = team_info["team"]["name"]


@st.cache_data(ttl=300)
def get_event_info(event_name):
    (event,) = [
        e
        for e in team_info["past_events"] + team_info["live_events"]
        if e["name"] == event_name
    ]
    return json.loads(
        BeautifulSoup(
            fetch(f"https://www.ballertv.com/events/{event['slug']}"),
            features="html.parser",
        ).select_one('div[data-react-class="profiles/events/ShowContainer"]')[
            "data-react-props"
        ]
    )


last_event_name = None
for s in team_info["past_streams"]:
    event_name = s["event_name"]

    if event_name != last_event_name:
        st.divider()
        event_info = get_event_info(event_name)
        event = event_info["event"]

        col1, col2, _ = st.columns([1, 4, 5])

        col1.image(event["logo"])

        col2.header(event_name)
        col2.write(f"### {event['date']}")

        last_event_name = event_name

    venue_name = s["venue_name"]
    start_time = s["start_time"]
    link = s["link"]

    our_team = (
        "team_1"
        if s["team_1_name"] == team_name
        else "team_2"
        if s["team_2_name"] == team_name
        else None
    )

    if our_team is None:
        raise ValueError(s)

    opposing_team = "team_2" if our_team == "team_1" else "team_1"
    opposing_team_name = s[f"{opposing_team}_name"]
    points_for = s[f"{our_team}_score"]
    points_against = s[f"{opposing_team}_score"]
    result = (
        ":trophy: Won"
        if points_for > points_against
        else "Tie"
        if points_for == points_against
        else "Lost"
    )
    is_won = points_for > points_against

    col1, col2 = st.columns([3, 7])
    col1.image(s["thumbnail"])

    with col2:
        if is_won:
            st.write(
                f"### [:trophy: :green[{team_name} vs {opposing_team_name}]]({s['link']})"
            )
        else:
            st.write(
                f"### [:confounded: :red[{team_name} vs {opposing_team_name}]]({s['link']})"
            )

        col1, col2, _ = st.columns([1, 1, 8])
        # col1.write(f"## :{'green' if points_for > points_against else 'red'}[{result}]")
        col1.metric(
            "Result", f"{points_for} : {points_against}", label_visibility="collapsed"
        )

        @st.fragment
        def load_video(link):
            if st.button("Load video", key=link):
                game_soup = BeautifulSoup(fetch(link))

                (game_info_div,) = game_soup.select(
                    'div[data-react-class="streams/ShowTypescript"]'
                )
                game_info = json.loads(game_info_div["data-react-props"])

                video_url = game_info["videoUrl"]

                components.html(
                    f"""
<html>
<head>
<link href="//vjs.zencdn.net/8.23.3/video-js.min.css" rel="stylesheet">
<script src="//vjs.zencdn.net/8.23.3/video.min.js"></script>
</head>
<body>
<video-js id=vid1 width=800 height=600 class="vjs-default-skin" controls>
    <source
    src="{video_url}"
    type="application/x-mpegURL">
</video-js>
<script>
var player = videojs('vid1');
</script>
</body>
</html>
""",
                    width=800,
                    height=600,
                )

                st.write(video_url)

        load_video(link)
