import { Flex, Tag } from 'antd';

export default function SkillTags({ skills }: { skills?: string[] | null }) {
  if (!skills || skills.length === 0) {
    return <span className="muted-inline-text">暂无技能标签</span>;
  }

  return (
    <Flex wrap="wrap" gap={8}>
      {skills.map((skill) => (
        <Tag key={skill} color="blue">
          {skill}
        </Tag>
      ))}
    </Flex>
  );
}
