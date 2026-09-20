import RuleList from "@/components/RuleList";

export default function RulesPage() {
  return (
    <>
      <h1>Draft rules</h1>
      <p>
        These rules come from initial team guidance and are <strong>not yet confirmed</strong>{" "}
        against the official style manual.
      </p>
      <RuleList />
    </>
  );
}
