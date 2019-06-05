# 概要

EC2, RDS のインスタンス個別、Auto Scaling のキャパシティの自動変更を平日の営業時間のみに起動するようにするスクリプト

- 祝日は日本の祝日のみの対応
- デフォルト
  - 起動: 平日9時 (CloudWatch rule で変更可能)
  - 終了: 毎日21時
  - 起動時
    - EC2: 起動
    - RDS: 起動
    - AutoScaling:
      - 希望するキャパシティ 1 (Lambda パラメータで変更可能)
      - 最小 1 (Lambda パラメータで変更可能)
      - 最大 4 (Lambda パラメータで変更可能)
  - 終了時
    - EC2: 終了 (AutoScaling 対象のインスタンスは 停止せず、ターミネートされ、別インスタンスが起動するため、AutoScaling で管理する必要あり)
    - RDS: 終了
    - AutoScaling:
      - 希望するキャパシティ 0 (Lambda パラメータで変更可能)
      - 最小 0 (Lambda パラメータで変更可能)
      - 最大 0 (Lambda パラメータで変更可能)


# 使い方

## lambda function のデプロイ

```
# lambda を保存する bucket を指定します: aws 全体でバケット名はユニークである必要があります
$ BUCKET=bucket-name
$ aws s3api create-bucket --acl private --bucket $BUCKET --region us-east-1
# Lambda を S3 にデプロイします
$ aws cloudformation package \
  --template-file StateScheduler-CloudFormation.yml \
  --s3-bucket $BUCKET \
  --output-template-file packaged-template.yml
```

## cloud formation のデプロイ

```
$ aws cloudformation deploy \
  --template-file packaged-template.yml \
  --stack-name StateScheduler \
  --capabilities CAPABILITY_NAMED_IAM CAPABILITY_IAM
```

## 自動起動・自動停止対象の EC2 を設定

- ブラウザで [EC2](https://ap-northeast-1.console.aws.amazon.com/ec2/v2/home#Instances:sort=instanceType) の画面を開く
- 自動起動、停止させたいインスタンスを選択
  - タグ追加
    - キー: state-scheduler
    - 値: True

## 自動起動・自動停止対象の RDS を設定

- ブラウザで [RDS](https://ap-northeast-1.console.aws.amazon.com/rds/home#databases:) の画面を開く
- 自動起動、停止させたいインスタンスを選択
  - タグ追加
    - キー: state-scheduler
    - 値: True

## 自動スケールアウト、スケールイン対象の AutoScaling グループを設定

- ブラウザで [AutoScaling](https://ap-northeast-1.console.aws.amazon.com/ec2/autoscaling/home?#AutoScalingGroups:view=details) の画面を開く
- 自動スケールアウト、スケールインさせたいグループを選択
  - タグ追加
    - キー: state-scheduler
    - 値: True
    - 新しいインスタンスにタグ付けする: いいえ

## 起動時間、終了時間を変更する

- 起動時間の変更
  - デフォルト値の起動時間を変更する場合、ブラウザで [CloudWatch-rule](https://ap-northeast-1.console.aws.amazon.com/cloudwatch/home?#rules:) にアクセス
  - StateScheduler-StartScheduledRule-*** のリンクを選択
  - アクションから編集をクリック、イベントソースに記載されている Cron式 の記述を変更 (UTC での動作となるので JST で考える場合は +9h する必要あり)
- 終了時間の変更
  - デフォルト値の起動時間を変更する場合、ブラウザで [CloudWatch-rule](https://ap-northeast-1.console.aws.amazon.com/cloudwatch/home?#rules:) にアクセス
  - StateScheduler-StopScheduledRule-*** のリンクを選択
  - アクションから編集をクリック、イベントソースに記載されている Cron式 の記述を変更 (UTC での動作となるので JST で考える場合は +9h する必要あり)
