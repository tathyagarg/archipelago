# Plans for the Bot

Database Structure:
```
User: {
  id: String,
  username: String,
  ships: [Ship]
}

Ship: {
  name: String,
  repo: URL,
  demo: URL,
  preview: URL,
  hours: Number,
  updates: [String],
}
```

```
+---------+      +---------+      +----------+
| Website |  ->  | Backend |  ->  | Database |
+---------+      +---------+      +----------+
                      |                ^
                      v                | Every 30 mins
                  +-------+            |
                  | Cache |  ----------+
                  +-------+
```


[ ] A database of projects
[ ] A cache
[ ] Database updates every 30 mins 
