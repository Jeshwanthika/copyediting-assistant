"use client";

import { useState } from "react";
import { addExample, deleteExample } from "@/lib/api";
import type { ExampleItem } from "@/types";

interface Props {
  ruleId: number;
  examples: ExampleItem[];
  onChanged: () => Promise<void>;
}

export default function ExampleManager({ ruleId, examples, onChanged }: Props) {
  const [input, setInput] = useState("");
  const [output, setOutput] = useState("");
  const [explanation, setExplanation] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function run(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
      await onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  async function handleAdd() {
    await run(async () => {
      await addExample(ruleId, {
        input_text: input,
        correct_output: output,
        explanation: explanation || undefined,
      });
      setInput("");
      setOutput("");
      setExplanation("");
    });
  }

  return (
    <div className="examples-editor">
      <h3>Examples</h3>
      {examples.length === 0 ? (
        <p>No example has been added yet.</p>
      ) : (
        <ul className="examples">
          {examples.map((example) => (
            <li key={example.id}>
              <p>
                <strong>Question:</strong> {example.input_text}
              </p>
              <p>
                <strong>Correct handling:</strong> {example.correct_output}
              </p>
              {example.explanation && (
                <p>
                  <strong>Explanation:</strong> {example.explanation}
                </p>
              )}
              <button className="secondary" onClick={() => run(() => deleteExample(ruleId, example.id))}>
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}

      <h4>Add an example</h4>
      <label className="field">
        <span>Question or input</span>
        <input type="text" value={input} onChange={(e) => setInput(e.target.value)} />
      </label>
      <label className="field">
        <span>Correct handling</span>
        <input type="text" value={output} onChange={(e) => setOutput(e.target.value)} />
      </label>
      <label className="field">
        <span>Explanation (optional)</span>
        <input type="text" value={explanation} onChange={(e) => setExplanation(e.target.value)} />
      </label>
      <button onClick={handleAdd}>Add example</button>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
