# **🕵️ AI Agentic Team: Case Study (Public Edition)**

**Challenge:** Agentic Observability & Failure Analysis

## **📋 The Mission**

Maintainers of high-velocity open-source projects like [OpenClaw](https://github.com/openclaw/openclaw) often face a growing backlog of closed, unmerged Pull Requests. Understanding the patterns behind these abandoned contributions is critical for improving project health and contributor experience.  
You are tasked with building the tooling to analyze why PRs are failing in the OpenClaw repository and ensuring all AI-generated code is tracked from the start.

**Note:** Focus on delivering a "Thin Thread"—a small, functioning end-to-end logic—then move to scaling, deep analysis, and optimization. We prioritize breadth and functional logic over perfect configuration.

## **🛠️ The Technical Requirements**

### **1\. AI Code Attribution (GitAI)**

We need to distinguish between human-written code and AI-assisted code across the entire lifecycle.

* **Task:** Install and configure the open-source version of **GitAI** in your local development environment for the case study repo.  
* **Objective:** Use GitAI to track all AI-generated code during this challenge. You must demonstrate how we can see the "AI percentage" of a PR and track that attribution.  
* **Note:** You may uninstall git-ai after completing the case study.

### **2\. The RCA Engine (Root Cause Analysis)**

Build a tool that identifies why OpenClaw PRs are abandoned. Begin by processing a subset of closed PRs as a Proof of Concept, then scale the analysis up or provide a technical roadmap for handling historical data at scale.

* **Data Sources:** Your tool should look at PR descriptions, diffs, CI/CD failure logs, the final human comments, or any other relevant metadata available before the PR was closed.  
* **Data Target:** Use the [OpenClaw GitHub org](https://github.com/openclaw/openclaw) as your data source.  
* **The Goal:** Output a reliable, grouped list of the top failure trends. Examples: "Stale/No Contributor Response," "Merge Conflicts," "CI/CD Failures," "Architectural Mismatch," or "Superseded by other PR." and so on

### **3\. Pipeline Integration & Scalability**

The tool shouldn't just run once on a laptop; it needs to be part of a sustainable engineering workflow.

* **Task:** Write a design document on how this system would run and be productionized.  
* **Scalability:** Describe how you plan to manage and reduce AI token consumption for cost-effective scaling.

## **📝 Instructions for Completion**

To submit your work, please use one of the following two methods:

### **Option A: Private GitHub Repository**

1. Create a **private** GitHub repository for your solution.  
2. Invite the following users as contributors: **povils** and **mKeRix**.  
3. Ensure all code and documentation are committed.

### **Option B: Compressed Archive (Tarball)**

If you prefer to submit via email, you must provide a compressed archive that includes your entire working directory, **including the .git folder** to preserve GitAI metadata.

* **Command to package your work:**

\# Run this from the root of your project directory  
tar \-czvf openclaw\_challenge\_submission.tar.gz .

* **Submission:** Send the resulting .tar.gz file to \[INSERT EMAIL HERE\].

*Any solution you build must be executable and verifiable. Ensure that core design decisions are explained so we can understand your thought process. If you do not manage to complete the implementation of a task in the allotted time, document your ideas and plans instead.*