import bz2
import networkx as nx
from multiprocessing import Pool, cpu_count
import time

def process_chunk(chunk):
    """
    Processes a chunk of the dataset and returns a subgraph.
    """
    subgraph = nx.DiGraph()
    for line in chunk:
        if line.startswith('#'):  # Skip comments
            continue
        parts = line.strip().split('|')
        if len(parts) != 3:  # Skip malformed lines
            continue
        as1, as2, relationship = parts
        try:
            as1 = int(as1)
            as2 = int(as2)
            relationship = int(relationship)
        except ValueError:  # Skip lines with invalid integers
            continue
        
        # Add edges based on the relationship
        if relationship == -1:  # Customer-to-provider
            subgraph.add_edge(as1, as2, relationship='customer')
        elif relationship == 0:  # Peer-to-peer
            subgraph.add_edge(as1, as2, relationship='peer')
            subgraph.add_edge(as2, as1, relationship='peer')
        elif relationship == 1:  # Provider-to-customer
            subgraph.add_edge(as2, as1, relationship='customer')
    
    return subgraph

def split_into_chunks(file_path, chunk_size=10000):
    """
    Splits the dataset into chunks for parallel processing.
    """
    chunks = []
    with bz2.open(file_path, 'rt') as f:
        chunk = []
        for line in f:
            chunk.append(line)
            if len(chunk) == chunk_size:
                chunks.append(chunk)
                chunk = []
        if chunk:  # Add the last chunk if it's not empty
            chunks.append(chunk)
    return chunks

def fetch_as_numbers(country_code, graph):
    """
    Fetches AS numbers for a given country from the graph.
    Reads AS numbers from files: as_pl.txt and as_tw.txt.
    """
    try:
        if country_code == "PL":  # Poland
            with open("as_pl.txt", "r") as file:
                as_numbers = [int(line.strip().replace("AS", "")) for line in file if line.strip()]
        elif country_code == "TW":  # taiwan
            with open("as_tw.txt", "r") as file:
                as_numbers = [int(line.strip().replace("AS", "")) for line in file if line.strip()]
        else:
            as_numbers = []
    except FileNotFoundError:
        print(f"Error: File for country code '{country_code}' not found.")
        as_numbers = []
    
    return as_numbers

def find_as_paths(graph, as_poland, as_taiwan):
    """
    Finds AS paths between ASes in Poland and Taiwan.
    """
    paths = []
    for as_pl in as_poland:
        if as_pl not in graph:
            print(f"Source AS {as_pl} is not in the graph.")
            continue
        for as_tw in as_taiwan:
            if as_tw not in graph:
                print(f"Target AS {as_tw} is not in the graph.")
                continue
            try:
                path = nx.shortest_path(graph, source=as_pl, target=as_tw)
                paths.append((as_pl, as_tw, path))
                print(f"Found path: {as_pl} -> {as_tw} via {path}")
            except nx.NetworkXNoPath:
                print(f"No path found between {as_pl} and {as_tw}.")
    return paths

def main():
    # Path to the CAIDA dataset file
    file_path = ".../20250301.as-rel.txt.bz2"  # Update this path
    
    # Step 1: Split the dataset into chunks
    print("Splitting dataset into chunks...")
    chunks = split_into_chunks(file_path, chunk_size=10000)
    print(f"Split dataset into {len(chunks)} chunks.")
    
    # Step 2: Process chunks in parallel
    print("Processing chunks in parallel...")
    start_time = time.time()
    with Pool(processes=cpu_count()) as pool:  # Use all available CPU cores
        subgraphs = pool.map(process_chunk, chunks)
    processing_time = time.time() - start_time
    print(f"Processed chunks in {processing_time:.2f} seconds.")
    
    # Step 3: Combine subgraphs into a single graph
    print("Combining subgraphs...")
    graph = nx.DiGraph()
    for subgraph in subgraphs:
        graph.update(subgraph)
    combining_time = time.time() - start_time - processing_time
    print(f"Combined subgraphs in {combining_time:.2f} seconds.")
    
    # Step 4: Fetch AS numbers for Poland and Taiwan
    print("Fetching AS numbers for Poland and taiwan...")
    as_poland = fetch_as_numbers("PL", graph)  # Poland
    as_taiwan = fetch_as_numbers("TW", graph)  # Taiwan
    print(f"Found {len(as_poland)} ASes in Poland and {len(as_taiwan)} ASes in taiwan.")
    
    # Step 5: Find AS paths between Poland and Taiwan
    print("Finding AS paths between Poland and Taiwan...")
    paths = find_as_paths(graph, as_poland, as_taiwan)
    
    # Step 6: Save paths to a file
    output_file = "as_paths_poland_taiwan.txt"
    with open(output_file, 'w') as f:
        for as_pl, as_tw, path in paths:
            f.write(f"{as_pl} -> {as_tw}: {' -> '.join(map(str, path))}\n")
    print(f"AS paths saved to {output_file}.")

if __name__ == "__main__":
    main()