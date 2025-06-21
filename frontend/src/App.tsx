import { Component, createSignal, createResource, For, Show } from "solid-js";
import "./App.css";

interface Tweet {
  id: number;
  content: string;
  topic: string;
  tone: string;
  created_at: string;
  status: string;
}

interface GenerateRequest {
  topic: string;
  tone: string;
  include_hashtags: boolean;
  target_audience: string;
}

const API_BASE = "http://localhost:8000";

const App: Component = () => {
  const [tweets, { mutate, refetch }] = createResource<Tweet[]>(fetchTweets);
  const [isGenerating, setIsGenerating] = createSignal(false);
  const [isPosting, setIsPosting] = createSignal(false);
  const [editingTweet, setEditingTweet] = createSignal<number | null>(null);
  const [editContent, setEditContent] = createSignal("");

  // Form state
  const [topic, setTopic] = createSignal("");
  const [tone, setTone] = createSignal("casual");
  const [includeHashtags, setIncludeHashtags] = createSignal(true);
  const [targetAudience, setTargetAudience] = createSignal("general");
  const [notification, setNotification] = createSignal<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  async function fetchTweets(): Promise<Tweet[]> {
    try {
      const response = await fetch(`${API_BASE}/tweets`);
      if (!response.ok) throw new Error("Failed to fetch tweets");
      return await response.json();
    } catch (error) {
      console.error("Error fetching tweets:", error);
      showNotification("error", "Failed to fetch tweets");
      return [];
    }
  }

  async function generateTweet() {
    if (!topic().trim()) {
      showNotification("error", "Please enter a topic");
      return;
    }

    setIsGenerating(true);
    try {
      const request: GenerateRequest = {
        topic: topic(),
        tone: tone(),
        include_hashtags: includeHashtags(),
        target_audience: targetAudience(),
      };

      const response = await fetch(`${API_BASE}/generate-tweet`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to generate tweet");
      }

      const newTweet = await response.json();
      showNotification("success", "Tweet generated successfully!");
      refetch();

      // Clear form
      setTopic("");
    } catch (error: any) {
      console.error("Error generating tweet:", error);
      showNotification("error", error.message || "Failed to generate tweet");
    } finally {
      setIsGenerating(false);
    }
  }

  async function editTweet(tweetId: number, content: string) {
    try {
      const response = await fetch(`${API_BASE}/edit-tweet/${tweetId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ tweet_id: tweetId, content }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to update tweet");
      }

      showNotification("success", "Tweet updated successfully!");
      setEditingTweet(null);
      setEditContent("");
      refetch();
    } catch (error: any) {
      console.error("Error editing tweet:", error);
      showNotification("error", error.message || "Failed to update tweet");
    }
  }

  async function postTweet(tweetId: number) {
    setIsPosting(true);
    try {
      const response = await fetch(`${API_BASE}/post-tweet/${tweetId}`, {
        method: "POST",
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to post tweet");
      }

      showNotification("success", "Tweet posted successfully!");
      refetch();
    } catch (error: any) {
      console.error("Error posting tweet:", error);
      showNotification("error", error.message || "Failed to post tweet");
    } finally {
      setIsPosting(false);
    }
  }

  async function deleteTweet(tweetId: number) {
    if (!confirm("Are you sure you want to delete this tweet?")) return;

    try {
      const response = await fetch(`${API_BASE}/tweets/${tweetId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete tweet");
      }

      showNotification("success", "Tweet deleted successfully!");
      refetch();
    } catch (error: any) {
      console.error("Error deleting tweet:", error);
      showNotification("error", error.message || "Failed to delete tweet");
    }
  }

  function showNotification(type: "success" | "error", message: string) {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  }

  function startEditing(tweet: Tweet) {
    setEditingTweet(tweet.id);
    setEditContent(tweet.content);
  }

  function cancelEditing() {
    setEditingTweet(null);
    setEditContent("");
  }

  return (
    <div class="app">
      {/* Notification */}
      <Show when={notification()}>
        <div class={`notification ${notification()?.type}`}>
          {notification()?.message}
        </div>
      </Show>

      <div class="container">
        <header class="header">
          <h1>🤖 AI Tweet Generator Agent</h1>
          <p>Generate, edit, and post tweets with AI assistance</p>
        </header>

        {/* Generation Form */}
        <div class="generator-card">
          <h2>Generate New Tweet</h2>

          <div class="form-group">
            <label for="topic">Topic / Content Idea</label>
            <input
              id="topic"
              type="text"
              placeholder="What should the tweet be about?"
              value={topic()}
              onInput={(e) => setTopic(e.currentTarget.value)}
              class="input-field"
            />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="tone">Tone</label>
              <select
                id="tone"
                value={tone()}
                onChange={(e) => setTone(e.currentTarget.value)}
                class="select-field"
              >
                <option value="casual">Casual</option>
                <option value="professional">Professional</option>
                <option value="humorous">Humorous</option>
                <option value="inspiring">Inspiring</option>
                <option value="informative">Informative</option>
              </select>
            </div>

            <div class="form-group">
              <label for="audience">Target Audience</label>
              <select
                id="audience"
                value={targetAudience()}
                onChange={(e) => setTargetAudience(e.currentTarget.value)}
                class="select-field"
              >
                <option value="general">General</option>
                <option value="tech">Tech Community</option>
                <option value="business">Business</option>
                <option value="creative">Creative</option>
                <option value="academic">Academic</option>
              </select>
            </div>
          </div>

          <div class="checkbox-group">
            <label class="checkbox-label">
              <input
                type="checkbox"
                checked={includeHashtags()}
                onChange={(e) => setIncludeHashtags(e.currentTarget.checked)}
              />
              Include relevant hashtags
            </label>
          </div>

          <button
            onClick={generateTweet}
            disabled={isGenerating() || !topic().trim()}
            class="btn btn-primary"
          >
            {isGenerating() ? (
              <>
                <div class="spinner"></div>
                Generating...
              </>
            ) : (
              "✨ Generate Tweet"
            )}
          </button>
        </div>

        {/* Tweets List */}
        <div class="tweets-section">
          <h2>Generated Tweets</h2>

          <Show
            when={tweets() && tweets()!.length > 0}
            fallback={
              <div class="empty-state">
                <p>
                  No tweets generated yet. Create your first AI-powered tweet
                  above! 🚀
                </p>
              </div>
            }
          >
            <div class="tweets-grid">
              <For each={tweets()}>
                {(tweet) => (
                  <div class={`tweet-card ${tweet.status}`}>
                    <div class="tweet-header">
                      <div class="tweet-meta">
                        <span class="topic-tag">{tweet.topic}</span>
                        <span class="tone-tag">{tweet.tone}</span>
                        <span class={`status-badge ${tweet.status}`}>
                          {tweet.status === "draft" ? "📝 Draft" : "✅ Posted"}
                        </span>
                      </div>
                      <div class="tweet-date">
                        {new Date(tweet.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    <div class="tweet-content">
                      <Show
                        when={editingTweet() === tweet.id}
                        fallback={<p class="tweet-text">{tweet.content}</p>}
                      >
                        <textarea
                          value={editContent()}
                          onInput={(e) => setEditContent(e.currentTarget.value)}
                          class="edit-textarea"
                          rows={4}
                          maxLength={280}
                        />
                        <div class="char-count">{editContent().length}/280</div>
                      </Show>
                    </div>

                    <div class="tweet-actions">
                      <Show
                        when={editingTweet() === tweet.id}
                        fallback={
                          <>
                            <Show when={tweet.status === "draft"}>
                              <button
                                onClick={() => startEditing(tweet)}
                                class="btn btn-secondary"
                              >
                                ✏️ Edit
                              </button>
                              <button
                                onClick={() => postTweet(tweet.id)}
                                disabled={isPosting()}
                                class="btn btn-success"
                              >
                                {isPosting() ? "🚀 Posting..." : "🚀 Post"}
                              </button>
                            </Show>
                            <button
                              onClick={() => deleteTweet(tweet.id)}
                              class="btn btn-danger"
                            >
                              🗑️ Delete
                            </button>
                          </>
                        }
                      >
                        <button
                          onClick={() => editTweet(tweet.id, editContent())}
                          disabled={
                            editContent().length === 0 ||
                            editContent().length > 280
                          }
                          class="btn btn-success"
                        >
                          💾 Save
                        </button>
                        <button
                          onClick={cancelEditing}
                          class="btn btn-secondary"
                        >
                          ❌ Cancel
                        </button>
                      </Show>
                    </div>
                  </div>
                )}
              </For>
            </div>
          </Show>
        </div>
      </div>
    </div>
  );
};

export default App;
