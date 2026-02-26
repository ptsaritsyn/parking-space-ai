import time
from app.agents.chat_agent import ChatAgent
from app.core.rag import RAGPipeline
from app.core.guard_rails import CarNumberPIIGuard
from app.db.sqlite_db import SQLiteDB
from app.db.pinecone_db import PineconeVectorDB
from app.llm.openai_llm import OpenAIClient
from dotenv import load_dotenv


load_dotenv()


def evaluate_latency(agent, test_queries, n_runs=3):
    print('evaluation latency test')
    latencies = []
    for query in test_queries:
        for _ in range(n_runs):
            start = time.time()
            _ = agent.run(query)
            end = time.time()
            latencies.append(end - start)
    avg_latency = sum(latencies) / len(latencies)
    return avg_latency, latencies


def evaluate_throughput(agent, test_queries, duration_sec=10):
    print('evaluation throughput test')
    count = 0
    start = time.time()
    while time.time() - start < duration_sec:
        for query in test_queries:
            _ = agent.run(query)
            count += 1
    throughput = count / duration_sec
    return throughput


def evaluate_accuracy(agent, test_cases):
    print('evaluation accuracy test')
    correct = 0
    for query, expected in test_cases:
        response = agent.run(query)
        if expected.lower() in response.lower():
            correct += 1
    accuracy = correct / len(test_cases)
    return accuracy


def main():
    vector_db = PineconeVectorDB()
    sql_db = SQLiteDB()
    llm = OpenAIClient()
    rag = RAGPipeline(vector_db=vector_db, llm=llm)
    guard = CarNumberPIIGuard()
    agent = ChatAgent(rag, guard, llm, sql_db)

    # Test queries
    test_queries = [
        "What are the working hours?",
        "How much does parking cost?",
        "Where is the parking located?",
        "How can I book a spot?"
    ]
    test_cases = [
        ("What are the working hours?", "08:00-22:00"),
        ("How much does parking cost?", "5 USD"),
        ("Where is the parking located?", "Central Street"),
        ("How can I book a spot?", "name, surname, car number, reservation period")
    ]

    avg_latency, latencies = evaluate_latency(agent, test_queries)
    throughput = evaluate_throughput(agent, test_queries)
    accuracy = evaluate_accuracy(agent, test_cases)

    # Generate Evaluation report
    report = f"""
    === System Performance Evaluation Report ===

    Average Latency: {avg_latency:.3f} sec
    Latencies: {latencies}
    Throughput: {throughput:.2f} requests/sec
    Accuracy: {accuracy:.2%}

    Test queries: {test_queries}
    """

    with open("evaluation_report.txt", "w") as f:
        f.write(report)

    print(report)


if __name__ == "__main__":
    main()
