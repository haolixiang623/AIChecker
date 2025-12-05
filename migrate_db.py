"""
数据库迁移脚本 - 添加验证字段到 PageElement 表
"""
import sqlite3
import os

DB_PATH = 'aichecker.db'

def migrate():
    """执行数据库迁移"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查是否已经有验证字段
        cursor.execute("PRAGMA table_info(pageelement)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'validated' in columns:
            print("✅ 验证字段已存在，无需迁移")
            return True
        
        print("开始数据库迁移...")
        
        # 添加验证相关字段
        migrations = [
            "ALTER TABLE pageelement ADD COLUMN validated INTEGER DEFAULT 0",
            "ALTER TABLE pageelement ADD COLUMN validation_time DATETIME",
            "ALTER TABLE pageelement ADD COLUMN status_code INTEGER",
            "ALTER TABLE pageelement ADD COLUMN response_time REAL",
            "ALTER TABLE pageelement ADD COLUMN validation_error TEXT",
            "ALTER TABLE pageelement ADD COLUMN clickable INTEGER",
            "ALTER TABLE pageelement ADD COLUMN enabled INTEGER"
        ]
        
        for migration in migrations:
            try:
                cursor.execute(migration)
                print(f"  ✅ {migration[:50]}...")
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e):
                    print(f"  ⚠️  列已存在，跳过")
                else:
                    raise
        
        conn.commit()
        print("✅ 数据库迁移完成!")
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
