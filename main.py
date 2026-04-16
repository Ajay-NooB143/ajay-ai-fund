from agents.inference_agent import run_inference
from agents.training_llama_agent import train_llama

def main():
    data = "market data sample"

    # Train model
    model = train_llama(data)
    print("Model:", model)

    # Run inference
    result = run_inference(data)
    print("Result:", result)

if __name__ == "__main__":
    main()
