from cassandra.cluster import Cluster

cluster = Cluster(['127.0.0.1'], port=9042)
session = cluster.connect()

# Run CQL file
with open('seed_data.cql', 'r', encoding='utf-8') as f:
    cql = f.read()

# naive split by semicolon; good enough for this seed file
for stmt in [s.strip() for s in cql.split(';') if s.strip()]:
    try:
        session.execute(stmt)
    except Exception as e:
        print('ERROR executing:', stmt[:80].replace('\n', ' '), '...', e)

cluster.shutdown()
print('Done')
