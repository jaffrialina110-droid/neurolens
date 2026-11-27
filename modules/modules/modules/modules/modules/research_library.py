
"""NeuroLens Research Library — Europe PMC search."""

import json
import urllib.parse
import urllib.request

import streamlit as st


API_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def search_papers(query, page_size=10):
    """Search Europe PMC for scientific publications."""

    params = urllib.parse.urlencode({
        "query": query,
        "format": "json",
        "pageSize": page_size,
        "resultType": "core",
    })

    request = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={"User-Agent": "NeuroLens-ResearchLibrary/1.0"},
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def get_authors(item):
    author_list = item.get("authorList", {}).get("author", [])

    if isinstance(author_list, dict):
        author_list = [author_list]

    names = [
        author.get("fullName", "")
        for author in author_list[:5]
        if author.get("fullName")
    ]

    return ", ".join(names) if names else "Authors not listed"


def render(st):
    st.title("📚 NeuroLens Research Library")

    st.write(
        "Search scientific literature in neuroscience, "
        "mental health, cognition and related fields."
    )

    if "nl_research_bookmarks" not in st.session_state:
        st.session_state.nl_research_bookmarks = {}

    query = st.text_input(
        "Research topic or keywords",
        placeholder="e.g. consciousness and attention",
        key="nl_research_query",
    )

    if st.button("Search research papers", type="primary"):
        if not query.strip():
            st.warning("Enter a research topic first.")
        else:
            try:
                with st.spinner("Searching Europe PMC..."):
                    data = search_papers(query.strip())

                st.session_state.nl_research_results = (
                    data.get("resultList", {}).get("result", [])
                )
                st.session_state.nl_research_query_done = query.strip()

            except Exception:
                st.error(
                    "Research search is temporarily unavailable. "
                    "Please check your internet connection and try again."
                )

    results = st.session_state.get(
        "nl_research_results", []
    )

    if results:
        st.subheader(
            f"Search results for: "
            f"{st.session_state.get('nl_research_query_done', '')}"
        )

        for index, paper in enumerate(results):
            title = paper.get("title", "Untitled paper")
            doi = paper.get("doi", "")
            paper_id = doi or paper.get("id", str(index))
            authors = get_authors(paper)
            journal = paper.get("journalTitle", "Journal not listed")
            year = paper.get("pubYear", "Year not listed")
            abstract = paper.get("abstractText", "")
            source = paper.get("source", "")
            article_id = paper.get("id", "")

            with st.container(border=True):
                st.markdown(f"### {title}")
                st.caption(f"{authors}")
                st.write(f"**Journal:** {journal}")
                st.write(f"**Year:** {year}")

                if doi:
                    st.write(f"**DOI:** {doi}")

                if abstract:
                    with st.expander("Read abstract"):
                        st.write(abstract)
                else:
                    st.caption("Abstract not available in this record.")

                if doi:
                    paper_url = f"https://doi.org/{doi}"
                elif source and article_id:
                    paper_url = (
                        "https://europepmc.org/article/"
                        f"{source}/{article_id}"
                    )
                else:
                    paper_url = "https://europepmc.org/"

                st.markdown(
                    f"[Open publication record]({paper_url})"
                )

                if st.button(
                    "Remove bookmark" if paper_id in
                    st.session_state.nl_research_bookmarks
                    else "Save to Research Book",
                    key=f"nl_bookmark_{index}_{paper_id}",
                ):
                    if paper_id in st.session_state.nl_research_bookmarks:
                        del st.session_state.nl_research_bookmarks[paper_id]
                    else:
                        st.session_state.nl_research_bookmarks[paper_id] = {
                            "title": title,
                            "authors": authors,
                            "journal": journal,
                            "year": year,
                            "doi": doi,
                            "url": paper_url,
                        }

                    st.rerun()

    st.divider()
    st.subheader("⭐ My Research Book")

    bookmarks = st.session_state.nl_research_bookmarks

    if bookmarks:
        for paper in bookmarks.values():
            st.markdown(f"**{paper['title']}**")
            st.caption(
                f"{paper['authors']} · {paper['journal']} · {paper['year']}"
            )
            st.markdown(f"[Open paper]({paper['url']})")
    else:
        st.caption("Your saved research papers will appear here.")

    st.caption(
        "Search and bookmarks currently use the active session. "
        "Permanent private storage and AI summaries will be integrated "
        "with the authenticated database in a later stage. "
        "Full-text access depends on publisher and open-access availability."
    )
